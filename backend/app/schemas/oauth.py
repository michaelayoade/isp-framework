from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """OAuth 2.0 Token Request"""

    grant_type: str = Field(..., description="OAuth grant type")
    username: Optional[str] = Field(None, description="Username for password grant")
    password: Optional[str] = Field(None, description="Password for password grant")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token for refresh grant"
    )
    scope: Optional[str] = Field(None, description="Requested scope")
    client_id: Optional[str] = Field(None, description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")
    code: Optional[str] = Field(None, description="Authorization code")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier")


class TokenResponse(BaseModel):
    """OAuth 2.0 Token Response"""

    access_token: str = Field(..., description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Granted scope")


class ClientCredentialsRequest(BaseModel):
    """OAuth 2.0 Client Credentials Request"""

    grant_type: str = Field(default="client_credentials")
    scope: Optional[str] = Field(None, description="Requested scope")


class TokenIntrospectionResponse(BaseModel):
    """OAuth 2.0 Token Introspection Response (RFC 7662)"""

    active: bool = Field(..., description="Whether the token is active")
    client_id: Optional[str] = Field(None, description="Client ID")
    username: Optional[str] = Field(None, description="Username")
    scope: Optional[str] = Field(None, description="Token scope")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    token_type: Optional[str] = Field(None, description="Token type")


class OAuthClientCreate(BaseModel):
    """Create OAuth Client Request"""

    client_name: str = Field(..., description="Client name")
    client_description: Optional[str] = Field(None, description="Client description")
    grant_types: str = Field(
        default="authorization_code,refresh_token", description="Supported grant types"
    )
    scopes: str = Field(
        default="customer_portal,admin_portal,api", description="Allowed scopes"
    )
    is_confidential: bool = Field(
        default=True, description="Whether client is confidential"
    )
    redirect_uris: Optional[str] = Field(
        None, description="Allowed redirect URIs (JSON array)"
    )


class OAuthClientResponse(BaseModel):
    """OAuth Client Response"""

    client_id: str
    client_name: str
    client_description: Optional[str]
    grant_types: list[str]
    scopes: list[str]
    is_active: bool
    is_confidential: bool
    created_at: datetime

    # Only returned on creation
    client_secret: Optional[str] = Field(
        None, description="Client secret (only on creation)"
    )


class AuthorizationCodeRequest(BaseModel):
    """OAuth 2.0 Authorization Code Request"""

    response_type: str = Field(default="code")
    client_id: str = Field(..., description="OAuth client ID")
    redirect_uri: str = Field(..., description="Redirect URI")
    scope: Optional[str] = Field(None, description="Requested scope")
    state: Optional[str] = Field(None, description="State parameter")
    code_challenge: Optional[str] = Field(None, description="PKCE code challenge")
    code_challenge_method: Optional[str] = Field(
        None, description="PKCE code challenge method"
    )


class AuthorizationCodeResponse(BaseModel):
    """OAuth 2.0 Authorization Code Response"""

    code: str = Field(..., description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")


class TokenRevocationRequest(BaseModel):
    """OAuth 2.0 Token Revocation Request (RFC 7009)"""

    token: str = Field(..., description="Token to revoke")
    token_type_hint: Optional[str] = Field(None, description="Token type hint")


class TokenRevocationResponse(BaseModel):
    """OAuth 2.0 Token Revocation Response"""

    revoked: bool = Field(..., description="Whether token was revoked")


class OAuthErrorResponse(BaseModel):
    """OAuth 2.0 Error Response"""

    error: str = Field(..., description="Error code")
    error_description: Optional[str] = Field(None, description="Error description")
    error_uri: Optional[str] = Field(None, description="Error information URI")
    state: Optional[str] = Field(None, description="State parameter")


# Scope definitions for documentation
class OAuthScopes:
    """OAuth 2.0 Scope definitions"""

    CUSTOMER_PORTAL = "customer_portal"
    ADMIN_PORTAL = "admin_portal"
    API = "api"
    READ = "read"
    WRITE = "write"

    @classmethod
    def get_all_scopes(cls) -> list[str]:
        return [cls.CUSTOMER_PORTAL, cls.ADMIN_PORTAL, cls.API, cls.READ, cls.WRITE]

    @classmethod
    def get_scope_descriptions(cls) -> dict[str, str]:
        return {
            cls.CUSTOMER_PORTAL: "Access to customer portal features",
            cls.ADMIN_PORTAL: "Access to admin portal features",
            cls.API: "Access to API endpoints",
            cls.READ: "Read-only access",
            cls.WRITE: "Write access",
        }
