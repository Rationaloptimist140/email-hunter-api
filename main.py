"""
Email Hunter API
A FastAPI service for extracting email addresses from text.

Endpoints:
- GET /: Health check
- POST /api/extract-emails: Extract emails from text (requires API key)
- POST /api/generate-key: Generate a test API key

Author: Email Hunter API Team
"""

from fastapi import FastAPI, HTTPException, status, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys
import os
import secrets
import hashlib
from datetime import datetime

# Add parent directory to path to import email_hunter module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from email_hunter import find_emails, hunt_emails
except ImportError:
    # Fallback for deployment environments
    import re
    from typing import List
    
    def find_emails(text: str) -> List[str]:
        """Extract all email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        seen = set()
        unique_emails = []
        for email in emails:
            email_lower = email.lower()
            if email_lower not in seen:
                seen.add(email_lower)
                unique_emails.append(email)
        return unique_emails
    
    def hunt_emails(text: str) -> dict:
        """Main function to hunt for emails in text."""
        emails = find_emails(text)
        return {
            "emails": emails,
            "count": len(emails),
            "text_length": len(text)
        }


# API Key Storage (in production, use a database)
# For demo purposes, we'll use an in-memory store
API_KEYS = {
    "demo_key_12345": {
        "name": "Demo Key",
        "created_at": "2026-02-16T00:00:00Z",
        "tier": "free"
    }
}

# Environment variable for master API keys (comma-separated)
MASTER_API_KEYS = os.getenv("API_KEYS", "").split(",")
if MASTER_API_KEYS and MASTER_API_KEYS[0]:
    for key in MASTER_API_KEYS:
        key = key.strip()
        if key:
            API_KEYS[key] = {
                "name": "Environment Key",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "tier": "premium"
            }


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Initialize FastAPI app
app = FastAPI(
    title="Email Hunter API",
    description="Extract email addresses from text with ease. Perfect for data cleaning, lead generation, and text processing.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS - allow all origins for maximum compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# API Key Authentication Dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> dict:
    """
    Verify API key from X-API-Key header.
    
    Args:
        x_api_key: API key from request header
        
    Returns:
        dict: API key information
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Missing API key",
                "detail": "API key is required. Include 'X-API-Key' header in your request.",
                "help": "Get a test API key from POST /api/generate-key"
            }
        )
    
    if x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Invalid API key",
                "detail": "The provided API key is not valid or has been revoked.",
                "help": "Generate a new API key from POST /api/generate-key"
            }
        )
    
    return API_KEYS[x_api_key]


# Pydantic Models for request/response validation
class EmailExtractionRequest(BaseModel):
    """Request model for email extraction endpoint."""
    text: str = Field(
        ...,
        description="The text to search for email addresses",
        min_length=1,
        max_length=1000000,  # 1MB text limit
        example="Contact us at support@company.com or sales@company.com. You can also reach John at john.doe@example.org"
    )
    
    @validator('text')
    def text_not_empty(cls, v):
        """Ensure text is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v


class EmailExtractionResponse(BaseModel):
    """Response model for email extraction endpoint."""
    success: bool = Field(description="Whether the extraction was successful")
    emails: List[str] = Field(description="List of unique email addresses found")
    count: int = Field(description="Number of unique emails found")
    text_length: int = Field(description="Length of input text processed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "emails": ["support@company.com", "sales@company.com", "john.doe@example.org"],
                "count": 3,
                "text_length": 156
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(description="Service status")
    service: str = Field(description="Service name")
    version: str = Field(description="API version")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "service": "Email Hunter API",
                "version": "1.0.0"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    detail: str = Field(default="", description="Additional error details")


class APIKeyGenerateRequest(BaseModel):
    """Request model for API key generation."""
    name: Optional[str] = Field(
        default="Test Key",
        description="Name/description for this API key",
        max_length=100,
        example="My Test Application"
    )


class APIKeyGenerateResponse(BaseModel):
    """Response model for API key generation."""
    success: bool = Field(description="Whether key generation was successful")
    api_key: str = Field(description="The generated API key")
    name: str = Field(description="Name of the API key")
    tier: str = Field(description="API tier (free/premium)")
    rate_limit: str = Field(description="Rate limit for this tier")
    created_at: str = Field(description="Creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "api_key": "test_key_abc123def456",
                "name": "My Test Application",
                "tier": "free",
                "rate_limit": "10 requests per minute",
                "created_at": "2026-02-16T09:30:00Z"
            }
        }


# API Endpoints

@app.get(
    "/",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API service is running and healthy",
    tags=["Health"]
)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        HealthResponse: Service status and information
    """
    return {
        "status": "ok",
        "service": "Email Hunter API",
        "version": "1.0.0"
    }


@app.post(
    "/api/extract-emails",
    response_model=EmailExtractionResponse,
    summary="Extract Emails from Text",
    description="Extract all email addresses from the provided text. Returns unique emails while preserving order. Requires API key authentication.",
    tags=["Email Extraction"],
    responses={
        200: {
            "description": "Successfully extracted emails",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "emails": ["support@company.com", "sales@company.com"],
                        "count": 2,
                        "text_length": 100
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - missing or invalid API key",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation error - invalid input",
            "model": ErrorResponse
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
@limiter.limit("10/minute")
async def extract_emails(
    request: Request,
    extraction_request: EmailExtractionRequest,
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Extract email addresses from text.
    
    This endpoint uses advanced regex pattern matching to find valid email addresses
    in the provided text. It handles various email formats and returns unique emails
    while preserving the order they appear.
    
    **Authentication Required**: Include 'X-API-Key' header with your API key.
    **Rate Limit**: 10 requests per minute per IP address (free tier).
    
    Args:
        request_obj: FastAPI Request object (for rate limiting)
        extraction_request: EmailExtractionRequest containing the text to process
        api_key_info: API key information from authentication
        
    Returns:
        EmailExtractionResponse with extracted emails and metadata
        
    Raises:
        HTTPException: If extraction fails or authentication/rate limit errors
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/extract-emails" \
             -H "X-API-Key: your_api_key_here" \
             -H "Content-Type: application/json" \
             -d '{"text": "Contact support@company.com or sales@company.com"}'
        ```
        
        Response:
        ```json
        {
            "success": true,
            "emails": ["support@company.com", "sales@company.com"],
            "count": 2,
            "text_length": 50
        }
        ```
    """
    try:
        # Extract emails using the imported function
        result = hunt_emails(extraction_request.text)
        
        # Return successful response
        return {
            "success": True,
            "emails": result["emails"],
            "count": result["count"],
            "text_length": result["text_length"]
        }
        
    except Exception as e:
        # Handle any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to extract emails",
                "detail": str(e)
            }
        )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Detailed Health Check",
    description="Detailed health check with service information",
    tags=["Health"]
)
async def detailed_health():
    """
    Detailed health check endpoint with additional service information.
    
    Returns:
        HealthResponse: Detailed service status and information
    """
    return {
        "status": "ok",
        "service": "Email Hunter API",
        "version": "1.0.0"
    }


@app.post(
    "/api/generate-key",
    response_model=APIKeyGenerateResponse,
    summary="Generate Test API Key",
    description="Generate a test API key for demo purposes. In production, this would require authentication.",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Successfully generated API key",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "api_key": "test_key_abc123def456",
                        "name": "My Test Application",
                        "tier": "free",
                        "rate_limit": "10 requests per minute",
                        "created_at": "2026-02-16T09:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def generate_api_key(request: APIKeyGenerateRequest = APIKeyGenerateRequest()):
    """
    Generate a test API key for demo purposes.
    
    **Note**: In production, this endpoint should require authentication
    and be integrated with a proper user management system.
    
    Args:
        request: APIKeyGenerateRequest with optional name
        
    Returns:
        APIKeyGenerateResponse with the generated API key
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/generate-key" \
             -H "Content-Type: application/json" \
             -d '{"name": "My Test App"}'
        ```
        
        Response:
        ```json
        {
            "success": true,
            "api_key": "test_key_abc123def456",
            "name": "My Test App",
            "tier": "free",
            "rate_limit": "10 requests per minute",
            "created_at": "2026-02-16T09:30:00Z"
        }
        ```
    """
    try:
        # Generate a random API key
        random_part = secrets.token_urlsafe(16)
        api_key = f"test_key_{random_part}"
        
        # Store the API key
        created_at = datetime.utcnow().isoformat() + "Z"
        API_KEYS[api_key] = {
            "name": request.name or "Test Key",
            "created_at": created_at,
            "tier": "free"
        }
        
        return {
            "success": True,
            "api_key": api_key,
            "name": request.name or "Test Key",
            "tier": "free",
            "rate_limit": "10 requests per minute",
            "created_at": created_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate API key",
                "detail": str(e)
            }
        )


# Error handlers

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": "Rate limit exceeded",
            "detail": "You have exceeded the rate limit of 10 requests per minute. Please wait and try again.",
            "help": "Upgrade to a premium tier for higher rate limits."
        }
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "detail": f"The requested endpoint {request.url.path} does not exist. Check /docs for available endpoints."
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors with custom response."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
