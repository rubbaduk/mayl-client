from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv

from .auth import AuthService
from .gmail_routes import gmail_router
from .models import UserSession

load_dotenv()

app = FastAPI(title="Gmail AI Assistant API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
auth_service = AuthService()

# Include routers
app.include_router(gmail_router, prefix="/api/gmail", tags=["gmail"])

@app.get("/")
async def root():
    return {"message": "Gmail AI Assistant API", "status": "running"}

@app.post("/api/auth/google")
async def authenticate_google(request: dict):
    # exchange Google JWT for OAuth URL (users need to authorize Gmail access)
    
    try:
        jwt_token = request.get("credential")
        if not jwt_token:
            raise HTTPException(status_code=400, detail="Missing credential")
        
        # validate JWT and get OAuth URL for Gmail permissions
        oauth_data = await auth_service.authenticate_user_jwt(jwt_token)
        
        return {
            "success": True,
            "requires_oauth": True,
            "oauth_url": oauth_data["authorization_url"],
            "state": oauth_data["state"],
            "message": oauth_data["message"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/api/auth/oauth-url")
async def get_oauth_url():
    """
    Get OAuth URL for Gmail authorization
    """
    try:
        oauth_data = auth_service.get_oauth_url()
        return oauth_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}")

@app.get("/api/auth/callback")
async def oauth_callback(code: str, state: str):
    """
    Handle OAuth callback and create user session
    """
    try:
        user_session = await auth_service.handle_oauth_callback(code, state)
        
        # redirect to frontend with session token
        frontend_url = f"http://localhost:5173/auth/success?token={user_session.session_token}"
        
        return {
            "success": True,
            "redirect_url": frontend_url,
            "user": user_session.user_info,
            "session_token": user_session.session_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OAuth callback failed: {str(e)}")

@app.post("/api/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and revoke session
    """
    try:
        success = await auth_service.logout_user(credentials.credentials)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Logout failed: {str(e)}")

@app.get("/api/user/profile")
async def get_user_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user profile
    """
    try:
        session = await auth_service.validate_session(credentials.credentials)
        return session.user_info
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid session")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
