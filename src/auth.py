"""
Authentication & Authorization
Secure API access with API keys and rate limiting
"""

import secrets
import hashlib
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, status, Depends, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, SecretStr, validator
import structlog

logger = structlog.get_logger()

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKey(BaseModel):
    """API Key model with metadata"""
    key_hash: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    rate_limit_per_minute: int = 100
    allowed_endpoints: Optional[List[str]] = None  # None = all endpoints

    def verify(self, provided_key: str) -> bool:
        """Verify provided key matches stored hash"""
        key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(key_hash, self.key_hash)


class APIKeyManager:
    """Manage API keys in-memory (or database in production)"""

    def __init__(self):
        self.keys: List[APIKey] = []
        self._load_keys()

    def _load_keys(self):
        """Load API keys from environment or database"""
        # In production, load from database
        # For now, create a default development key

        # Development key: "tune_dev_key_12345"
        dev_key_hash = hashlib.sha256("tune_dev_key_12345".encode()).hexdigest()
        self.keys.append(APIKey(
            key_hash=dev_key_hash,
            name="Development Key",
            created_at=datetime.utcnow(),
            rate_limit_per_minute=100
        ))

        logger.info(
            "api_keys_loaded",
            count=len(self.keys),
            note="Using development keys. Set production keys in .env"
        )

    def create_key(
        self,
        name: str,
        rate_limit_per_minute: int = 100,
        allowed_endpoints: Optional[List[str]] = None
    ) -> tuple[str, APIKey]:
        """Create new API key

        Returns:
            Tuple of (plaintext_key, api_key_object)
            WARNING: Plaintext key returned only once!
        """
        # Generate secure random key
        plaintext_key = f"tune_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            created_at=datetime.utcnow(),
            rate_limit_per_minute=rate_limit_per_minute,
            allowed_endpoints=allowed_endpoints
        )

        self.keys.append(api_key)

        logger.info(
            "api_key_created",
            name=name,
            rate_limit=rate_limit_per_minute
        )

        return plaintext_key, api_key

    def verify_key(self, provided_key: str) -> Optional[APIKey]:
        """Verify API key and return key object if valid"""
        for api_key in self.keys:
            if api_key.is_active and api_key.verify(provided_key):
                # Update last used timestamp
                api_key.last_used_at = datetime.utcnow()
                return api_key
        return None

    def revoke_key(self, key_hash: str):
        """Revoke (deactivate) an API key"""
        for api_key in self.keys:
            if api_key.key_hash == key_hash:
                api_key.is_active = False
                logger.warning("api_key_revoked", name=api_key.name)
                return True
        return False


# Global key manager
key_manager = APIKeyManager()


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header)
) -> APIKey:
    """Dependency to verify API key

    Usage:
        @app.get("/protected")
        async def protected_route(api_key: APIKey = Depends(verify_api_key)):
            # api_key is validated APIKey object
            pass
    """
    if not api_key:
        logger.warning(
            "missing_api_key",
            path=request.url.path,
            client=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Verify key
    validated_key = key_manager.verify_key(api_key)

    if not validated_key:
        logger.warning(
            "invalid_api_key",
            path=request.url.path,
            client=request.client.host,
            key_prefix=api_key[:10] if api_key else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Check endpoint permissions if restricted
    if validated_key.allowed_endpoints:
        if request.url.path not in validated_key.allowed_endpoints:
            logger.warning(
                "unauthorized_endpoint",
                key_name=validated_key.name,
                path=request.url.path,
                allowed=validated_key.allowed_endpoints
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key not authorized for endpoint: {request.url.path}"
            )

    logger.info(
        "api_key_validated",
        key_name=validated_key.name,
        path=request.url.path
    )

    return validated_key


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""
    pass


class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""

    def __init__(self):
        self.requests = {}  # {key_hash: [(timestamp, count), ...]}

    async def check_rate_limit(
        self,
        api_key: APIKey,
        window_seconds: int = 60
    ) -> bool:
        """Check if request is within rate limit

        Args:
            api_key: Validated API key
            window_seconds: Time window for rate limiting (default 60s)

        Returns:
            True if within limit

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        now = datetime.utcnow()
        key_hash = api_key.key_hash

        # Clean old entries
        if key_hash in self.requests:
            cutoff = now - timedelta(seconds=window_seconds)
            self.requests[key_hash] = [
                (ts, count) for ts, count in self.requests[key_hash]
                if ts > cutoff
            ]
        else:
            self.requests[key_hash] = []

        # Count requests in window
        total_requests = sum(count for _, count in self.requests[key_hash])

        # Check limit
        if total_requests >= api_key.rate_limit_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                key_name=api_key.name,
                requests_in_window=total_requests,
                limit=api_key.rate_limit_per_minute
            )
            raise RateLimitExceeded(
                f"Rate limit exceeded: {api_key.rate_limit_per_minute} requests per minute"
            )

        # Add current request
        self.requests[key_hash].append((now, 1))

        return True


# Global rate limiter
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    api_key: APIKey = Depends(verify_api_key)
) -> APIKey:
    """Dependency to check rate limit after auth

    Usage:
        @app.get("/api/endpoint")
        async def endpoint(api_key: APIKey = Depends(check_rate_limit)):
            # Request is authenticated AND within rate limit
            pass
    """
    try:
        await rate_limiter.check_rate_limit(api_key)
        return api_key
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(api_key.rate_limit_per_minute),
                "X-RateLimit-Remaining": "0"
            }
        )


# Combined dependency: auth + rate limiting
async def require_auth(
    request: Request,
    api_key: APIKey = Depends(verify_api_key)
) -> APIKey:
    """Combined auth + rate limiting dependency

    This is the recommended dependency for all protected endpoints.

    Usage:
        @app.post("/api/prospects/analyze")
        async def analyze(
            prospect: ProspectInput,
            api_key: APIKey = Depends(require_auth)
        ):
            # Fully protected endpoint
            pass
    """
    return await check_rate_limit(request, api_key)


def get_api_key_for_testing() -> str:
    """Get development API key for testing

    Usage in tests:
        headers = {"X-API-Key": get_api_key_for_testing()}
        response = client.get("/api/endpoint", headers=headers)
    """
    return "tune_dev_key_12345"


# Example: Create production keys
def create_production_keys():
    """Create production API keys (run once during setup)"""

    # Customer key with full access
    customer_key, _ = key_manager.create_key(
        name="Production Customer Key",
        rate_limit_per_minute=100
    )
    print(f"Customer API Key (save this!): {customer_key}")

    # Internal automation key with higher rate limit
    internal_key, _ = key_manager.create_key(
        name="Internal Automation",
        rate_limit_per_minute=1000
    )
    print(f"Internal API Key (save this!): {internal_key}")

    # Restricted key for specific endpoints only
    webhook_key, _ = key_manager.create_key(
        name="Clay Webhook Handler",
        rate_limit_per_minute=50,
        allowed_endpoints=["/api/clay/webhook"]
    )
    print(f"Webhook API Key (save this!): {webhook_key}")

    print("\n⚠️  WARNING: These keys are shown only once! Save them securely.")
    print("Add them to your .env file:")
    print(f"CUSTOMER_API_KEY={customer_key}")
    print(f"INTERNAL_API_KEY={internal_key}")
    print(f"WEBHOOK_API_KEY={webhook_key}")


if __name__ == "__main__":
    # Generate production keys
    print("Generating production API keys...\n")
    create_production_keys()
