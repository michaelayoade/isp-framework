from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.oauth import OAuthService
from app.schemas.oauth import (
    TokenResponse as OAuthTokenResponse,
    TokenRequest,
    ClientCredentialsRequest,
    TokenIntrospectionResponse
)
import logging
import base64

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBasic()


def get_client_credentials(request: Request) -> tuple[str, str]:
    """Extract client credentials from Authorization header or request body"""
    auth_header = request.headers.get("authorization")
    
    if auth_header and auth_header.startswith("Basic "):
        # Extract from Authorization header (RFC 6749 Section 2.3.1)
        try:
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            client_id, client_secret = decoded_credentials.split(":", 1)
            return client_id, client_secret
        except Exception as e:
            logger.warning(f"Failed to parse Basic auth header: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client credentials format"
            )
    
    return None, None


@router.post("/token", response_model=OAuthTokenResponse)
async def oauth_token(
    request: Request,
    grant_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 Token Endpoint
    
    Supports multiple grant types:
    - password: Resource Owner Password Credentials Grant
    - refresh_token: Refresh Token Grant
    - client_credentials: Client Credentials Grant
    - authorization_code: Authorization Code Grant (future)
    """
    oauth_service = OAuthService(db)
    
    # Extract client credentials (from header or form)
    header_client_id, header_client_secret = get_client_credentials(request)
    final_client_id = client_id or header_client_id
    final_client_secret = client_secret or header_client_secret
    
    if not final_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID is required"
        )
    
    # Authenticate client
    client = oauth_service.authenticate_client(final_client_id, final_client_secret)
    if not client:
        logger.warning(f"Client authentication failed: {final_client_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Check if grant type is supported by client
    supported_grants = client.grant_types.split(",")
    if grant_type not in supported_grants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grant type '{grant_type}' not supported by client"
        )
    
    try:
        if grant_type == "password":
            # Resource Owner Password Credentials Grant
            if not username or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username and password are required for password grant"
                )
            
            token_data = oauth_service.password_grant_flow(
                client=client,
                username=username,
                password=password,
                scope=scope
            )
            
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )
            
            return OAuthTokenResponse(**token_data)
        
        elif grant_type == "refresh_token":
            # Refresh Token Grant
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refresh token is required"
                )
            
            new_token = oauth_service.refresh_access_token(refresh_token)
            if not new_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            return OAuthTokenResponse(
                access_token=new_token.access_token,
                refresh_token=new_token.refresh_token,
                token_type="Bearer",
                expires_in=int((new_token.expires_at - new_token.created_at).total_seconds()),
                scope=new_token.scope
            )
        
        elif grant_type == "client_credentials":
            # Client Credentials Grant
            token_data = oauth_service.client_credentials_flow(
                client=client,
                scope=scope
            )
            
            return OAuthTokenResponse(**token_data)
        
        elif grant_type == "authorization_code":
            # Authorization Code Grant
            if not code or not redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Authorization code and redirect URI are required"
                )
            
            token_data = oauth_service.exchange_authorization_code(
                client=client,
                code=code,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )
            
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid authorization code"
                )
            
            return OAuthTokenResponse(**token_data)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported grant type: {grant_type}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/revoke")
async def revoke_token(
    request: Request,
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 Token Revocation Endpoint (RFC 7009)
    """
    oauth_service = OAuthService(db)
    
    # Extract client credentials
    header_client_id, header_client_secret = get_client_credentials(request)
    final_client_id = client_id or header_client_id
    final_client_secret = client_secret or header_client_secret
    
    if not final_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID is required"
        )
    
    # Authenticate client
    client = oauth_service.authenticate_client(final_client_id, final_client_secret)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Revoke token
    success = oauth_service.revoke_token(token)
    
    # RFC 7009: The authorization server responds with HTTP status code 200
    # regardless of whether the token was successfully revoked
    return {"revoked": success}


@router.post("/introspect", response_model=TokenIntrospectionResponse)
async def introspect_token(
    request: Request,
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 Token Introspection Endpoint (RFC 7662)
    """
    oauth_service = OAuthService(db)
    
    # Extract client credentials
    header_client_id, header_client_secret = get_client_credentials(request)
    final_client_id = client_id or header_client_id
    final_client_secret = client_secret or header_client_secret
    
    if not final_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID is required"
        )
    
    # Authenticate client
    client = oauth_service.authenticate_client(final_client_id, final_client_secret)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Introspect token
    introspection_data = oauth_service.introspect_token(token)
    
    return TokenIntrospectionResponse(**introspection_data)


@router.get("/clients/{client_id}")
async def get_client_info(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    Get OAuth client information (for debugging/admin purposes)
    """
    oauth_service = OAuthService(db)
    client = oauth_service.client_repo.get_by_field("client_id", client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "client_description": client.client_description,
        "grant_types": client.grant_types.split(","),
        "scopes": client.scopes.split(","),
        "is_active": client.is_active,
        "is_confidential": client.is_confidential,
        "created_at": client.created_at
    }
