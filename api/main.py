import os
from dotenv import load_dotenv

# load environment variables first, before any other imports
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

app = FastAPI(title="gmail ai assistant api", version="1.0.0")

# cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "gmail ai assistant api working"}

# import auth service after dotenv is loaded
from .auth import AuthService
auth_service = AuthService()

@app.get("/api/auth/oauth-url")
async def get_oauth_url():
    try:
        url = auth_service.get_authorization_url()
        return {"authorization_url": url}
    except Exception as e:
        raise HTTPException(500, f"error creating oauth url: {str(e)}")

@app.get("/api/auth/callback")
async def handle_oauth_callback(code: str = None, error: str = None):
    if error:
        raise HTTPException(400, f"oauth error: {error}")
    
    if not code:
        raise HTTPException(400, "authorization code required")
    
    try:
        session_token = await auth_service.handle_oauth_callback(code)
        return RedirectResponse(url=f"http://localhost:5173?token={session_token}")
    except Exception as e:
        raise HTTPException(500, f"oauth callback failed: {str(e)}")

# include gmail routes
from .gmail_routes import router as gmail_router
app.include_router(gmail_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
