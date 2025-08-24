import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from fastapi import HTTPException

class AuthService:
    def __init__(self):
        # load dotenv from the correct path
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        # also try loading from parent directory as backup
        if not os.path.exists(env_path):
            parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            load_dotenv(parent_env)
        
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET") 
        self.redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/api/auth/callback")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.scopes = [
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://mail.google.com/'
        ]
        
        # debug print to see what's loaded
        print(f"looking for .env at: {env_path}")
        print(f".env exists: {os.path.exists(env_path)}")
        print(f"loaded environment variables:")
        print(f"  client_id: {self.client_id}")
        print(f"  client_secret exists: {bool(self.client_secret)}")
        print(f"  jwt_secret exists: {bool(self.jwt_secret)}")
        
        self._sessions = {}
        
        if not self.client_id or not self.client_secret or not self.jwt_secret:
            print("error: missing required environment variables")
            print(f"  GOOGLE_CLIENT_ID: {'✓' if self.client_id else '✗'}")
            print(f"  GOOGLE_CLIENT_SECRET: {'✓' if self.client_secret else '✗'}")
            print(f"  JWT_SECRET_KEY: {'✓' if self.jwt_secret else '✗'}")
            raise Exception("missing oauth credentials in .env file")
    
    def create_oauth_flow(self):
        """create oauth flow for gmail api access"""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(client_config, scopes=self.scopes)
        flow.redirect_uri = self.redirect_uri
        return flow
    
    def get_authorization_url(self):
        """generate oauth authorization url"""
        flow = self.create_oauth_flow()
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url
    
    async def handle_oauth_callback(self, authorization_code: str):
        """handle oauth callback and create session with gmail access"""
        try:
            flow = self.create_oauth_flow()
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            user_info = self.get_user_info(credentials)
            
            session_data = {
                "user_id": user_info["id"],
                "email": user_info["email"],
                "name": user_info.get("name", ""),
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": self.scopes
            }
            
            session_token = self.create_session_token(session_data)
            self._sessions[session_token] = session_data
            
            return session_token
            
        except Exception as e:
            raise HTTPException(400, f"oauth callback failed: {str(e)}")
    
    def get_user_info(self, credentials):
        """get user information from google"""
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    
    def create_session_token(self, user_data: dict) -> str:
        """create jwt session token"""
        payload = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    async def validate_session(self, token: str) -> dict:
        """validate session token and return session data"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            session_data = self._sessions.get(token)
            if not session_data:
                raise HTTPException(401, "session not found")
            
            return session_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "invalid token")
