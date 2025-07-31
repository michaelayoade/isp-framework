import secrets
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash
from app.models import Administrator, OAuthClient, OAuthToken, OAuthAuthorizationCode
from app.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class OAuthService:
    """OAuth 2.0 service for handling authentication flows"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client_repo = BaseRepository(OAuthClient, db)
        self.token_repo = BaseRepository(OAuthToken, db)
        self.code_repo = BaseRepository(OAuthAuthorizationCode, db)
        self.admin_repo = BaseRepository(Administrator, db)

    # OAuth Client Management
    def create_oauth_client(
        self,
        client_name: str,
        client_description: str = None,
        grant_types: str = "authorization_code,refresh_token",
        scopes: str = "customer_portal,admin_portal,api",
        is_confidential: bool = True
    ) -> OAuthClient:
        """Create a new OAuth client"""
        client_id = self._generate_client_id()
        client_secret = self._generate_client_secret() if is_confidential else None
        
        client_data = {
            "client_id": client_id,
            "client_secret": get_password_hash(client_secret) if client_secret else None,
            "client_name": client_name,
            "client_description": client_description,
            "grant_types": grant_types,
            "scopes": scopes,
            "is_confidential": is_confidential
        }
        
        client = self.client_repo.create(client_data)
        logger.info(f"Created OAuth client: {client_name} ({client_id})")
        
        # Return client with plain text secret for initial setup
        client.plain_client_secret = client_secret
        return client

    def authenticate_client(self, client_id: str, client_secret: str = None) -> Optional[OAuthClient]:
        """Authenticate OAuth client"""
        client = self.client_repo.get_by_field("client_id", client_id)
        if not client or not client.is_active:
            return None
            
        # Public clients don't require secret verification
        if not client.is_confidential:
            return client
            
        # Confidential clients must provide valid secret
        if not client_secret or not verify_password(client_secret, client.client_secret):
            logger.warning(f"Invalid client secret for client: {client_id}")
            return None
            
        return client

    def validate_grant_type(self, client: OAuthClient, grant_type: str) -> bool:
        """Validate if client supports the requested grant type"""
        if not client.grant_types:
            return False
            
        allowed_grants = set(grant.strip() for grant in client.grant_types.split(","))
        if grant_type not in allowed_grants:
            logger.warning(f"Grant type '{grant_type}' not allowed for client: {client.client_id}")
            return False
            
        return True

    def validate_scope(self, client: OAuthClient, requested_scope: str = None) -> bool:
        """Validate if requested scope is allowed for client"""
        if not requested_scope:
            return True  # No scope requested is always valid
            
        if not client.scopes:
            logger.warning(f"No scopes configured for client: {client.client_id}")
            return False
            
        allowed_scopes = set(scope.strip() for scope in client.scopes.split(","))
        requested_scopes = set(scope.strip() for scope in requested_scope.split())
        
        if not requested_scopes.issubset(allowed_scopes):
            invalid_scopes = requested_scopes - allowed_scopes
            logger.warning(f"Invalid scopes {invalid_scopes} for client: {client.client_id}")
            return False
            
        return True

    # Token Generation and Management
    def generate_access_token(
        self,
        client: OAuthClient,
        user: Administrator = None,
        scope: str = None,
        expires_in: int = 3600  # 1 hour default
    ) -> OAuthToken:
        """Generate OAuth access token"""
        access_token = self._generate_token()
        refresh_token = self._generate_token()
        
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=30)  # 30 days for refresh
        
        token_data = {
            "client_id": client.client_id,
            "user_id": user.id if user else None,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scope": scope or client.scopes,
            "expires_at": expires_at,
            "refresh_expires_at": refresh_expires_at
        }
        
        token = self.token_repo.create(token_data)
        logger.info(f"Generated access token for client: {client.client_id}")
        return token

    def validate_access_token(self, access_token: str) -> Optional[OAuthToken]:
        """Validate OAuth access token"""
        token = self.token_repo.get_by_field("access_token", access_token)
        
        if not token or token.is_revoked:
            return None
            
        if datetime.now(timezone.utc) > token.expires_at:
            logger.info(f"Access token expired: {access_token[:10]}...")
            return None
            
        return token

    def refresh_access_token(self, refresh_token: str) -> Optional[OAuthToken]:
        """Refresh OAuth access token"""
        old_token = self.token_repo.get_by_field("refresh_token", refresh_token)
        
        if not old_token or old_token.is_revoked:
            return None
            
        if datetime.now(timezone.utc) > old_token.refresh_expires_at:
            logger.info(f"Refresh token expired: {refresh_token[:10]}...")
            return None
            
        # Get client for new token generation
        client = self.client_repo.get_by_field("client_id", old_token.client_id)
        if not client:
            return None
            
        # Get user if token was user-associated
        user = None
        if old_token.user_id:
            user = self.admin_repo.get(old_token.user_id)
            
        # Revoke old token
        self.revoke_token(old_token.access_token)
        
        # Generate new token
        new_token = self.generate_access_token(
            client=client,
            user=user,
            scope=old_token.scope
        )
        
        logger.info(f"Refreshed access token for client: {client.client_id}")
        return new_token

    def revoke_token(self, token: str) -> bool:
        """Revoke OAuth token"""
        oauth_token = self.token_repo.get_by_field("access_token", token)
        if not oauth_token:
            oauth_token = self.token_repo.get_by_field("refresh_token", token)
            
        if oauth_token and not oauth_token.is_revoked:
            update_data = {
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc)
            }
            self.token_repo.update(oauth_token.id, update_data)
            logger.info(f"Revoked token: {token[:10]}...")
            return True
            
        return False

    # OAuth Flows
    def password_grant_flow(
        self,
        client: OAuthClient,
        username: str,
        password: str,
        scope: str = None
    ) -> Optional[Dict[str, Any]]:
        """Handle OAuth password grant flow"""
        # Validate grant type
        if not self.validate_grant_type(client, "password"):
            raise ValueError("invalid_grant: password grant not allowed for this client")
            
        # Validate scope
        if not self.validate_scope(client, scope):
            raise ValueError("invalid_scope: requested scope not allowed for this client")
            
        # Authenticate user
        user = self.admin_repo.get_by_field("username", username)
        if not user or not user.is_active:
            return None
            
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            return None
            
        # Update last login
        self.admin_repo.update(user.id, {"last_login": datetime.now(timezone.utc)})
        
        # Generate token
        token = self.generate_access_token(
            client=client,
            user=user,
            scope=scope
        )
        
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": "Bearer",
            "expires_in": int((token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "scope": token.scope
        }

    def client_credentials_flow(
        self,
        client: OAuthClient,
        scope: str = None
    ) -> Dict[str, Any]:
        """Handle OAuth client credentials flow"""
        # Validate grant type
        if not self.validate_grant_type(client, "client_credentials"):
            raise ValueError("invalid_grant: client_credentials grant not allowed for this client")
            
        # Validate scope
        if not self.validate_scope(client, scope):
            raise ValueError("invalid_scope: requested scope not allowed for this client")
            
        # Public clients should not use client_credentials
        if not client.is_confidential:
            logger.warning(f"Public client {client.client_id} attempted client_credentials flow")
            raise ValueError("invalid_client: public clients cannot use client_credentials grant")
            
        # Generate token without user association
        token = self.generate_access_token(
            client=client,
            user=None,
            scope=scope
        )
        
        return {
            "access_token": token.access_token,
            "token_type": "Bearer",
            "expires_in": int((token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "scope": token.scope
        }

    # Authorization Code Flow (for future web-based OAuth)
    def create_authorization_code(
        self,
        client: OAuthClient,
        user: Administrator,
        redirect_uri: str,
        scope: str = None,
        code_challenge: str = None,
        code_challenge_method: str = None
    ) -> OAuthAuthorizationCode:
        """Create authorization code for OAuth flow"""
        code = self._generate_authorization_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)  # 10 minutes
        
        code_data = {
            "code": code,
            "client_id": client.client_id,
            "user_id": user.id,
            "redirect_uri": redirect_uri,
            "scope": scope or client.scopes,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "expires_at": expires_at
        }
        
        auth_code = self.code_repo.create(code_data)
        logger.info(f"Created authorization code for client: {client.client_id}")
        return auth_code

    def exchange_authorization_code(
        self,
        client: OAuthClient,
        code: str,
        redirect_uri: str,
        code_verifier: str = None
    ) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        auth_code = self.code_repo.get_by_field("code", code)
        
        if not auth_code or auth_code.is_used:
            return None
            
        if datetime.now(timezone.utc) > auth_code.expires_at:
            logger.info(f"Authorization code expired: {code[:10]}...")
            return None
            
        if auth_code.client_id != client.client_id:
            logger.warning(f"Client mismatch for authorization code: {code[:10]}...")
            return None
            
        if auth_code.redirect_uri != redirect_uri:
            logger.warning(f"Redirect URI mismatch for authorization code: {code[:10]}...")
            return None
            
        # Verify PKCE if used
        if auth_code.code_challenge and code_verifier:
            if not self._verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
                logger.warning(f"PKCE verification failed for code: {code[:10]}...")
                return None
                
        # Mark code as used
        self.code_repo.update(auth_code.id, {
            "is_used": True,
            "used_at": datetime.now(timezone.utc)
        })
        
        # Get user
        user = self.admin_repo.get(auth_code.user_id)
        if not user:
            return None
            
        # Generate token
        token = self.generate_access_token(
            client=client,
            user=user,
            scope=auth_code.scope
        )
        
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": "Bearer",
            "expires_in": int((token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "scope": token.scope
        }

    # Utility Methods
    def _generate_client_id(self) -> str:
        """Generate unique client ID"""
        return f"client_{secrets.token_urlsafe(16)}"

    def _generate_client_secret(self) -> str:
        """Generate client secret"""
        return secrets.token_urlsafe(32)

    def _generate_token(self) -> str:
        """Generate access/refresh token"""
        return secrets.token_urlsafe(32)

    def _generate_authorization_code(self) -> str:
        """Generate authorization code"""
        return secrets.token_urlsafe(16)

    def _verify_pkce(self, code_verifier: str, code_challenge: str, method: str) -> bool:
        """Verify PKCE code challenge"""
        if method == "S256":
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
            return challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        return False

    # Token Introspection
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """Introspect OAuth token (RFC 7662)"""
        oauth_token = self.validate_access_token(token)
        
        if not oauth_token:
            return {"active": False}
            
        self.client_repo.get_by_field("client_id", oauth_token.client_id)
        user = None
        if oauth_token.user_id:
            user = self.admin_repo.get(oauth_token.user_id)
            
        return {
            "active": True,
            "client_id": oauth_token.client_id,
            "username": user.username if user else None,
            "scope": oauth_token.scope,
            "exp": int(oauth_token.expires_at.timestamp()),
            "iat": int(oauth_token.created_at.timestamp()),
            "token_type": oauth_token.token_type
        }
