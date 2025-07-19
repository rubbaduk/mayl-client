import os
import jwt
import httpx
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from google.auth.transport import requests
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from models import UserInfo, UserSession

class AuthService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
        self.sessions: Dict[str, UserSession] = {}  # in-memory storage (USE REDIS WHEN DEPLOYING)
        self.oauth_states: Dict[str, str] = {}  # store OAuth state tokens
        
        # Gmail API scopes
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
    def create_oauth_flow(self):
        # create OAuth flow for Gmail API access
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        return flow
        
    def get_oauth_url(self) -> Dict[str, str]:
        # generate OAuth URL for user authorization
        flow = self.create_oauth_flow()
        
        # generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        # store state for validation
        self.oauth_states[state] = datetime.utcnow().isoformat()
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    
    async def handle_oauth_callback(self, code: str, state: str) -> UserSession:
        # handle OAuth callback and create user session"""
        
        # validate state parameter
        if state not in self.oauth_states:
            raise Exception("Invalid OAuth state")
        
        # remove used state
        del self.oauth_states[state]
        
        # exchange code for tokens
        flow = self.create_oauth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Get user info from the credentials
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Create user info object
        user_info_obj = UserInfo(
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info.get('picture'),
            google_id=user_info['id']
        )
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Create user session with credentials
        user_session = UserSession(
            user_info=user_info_obj,
            session_token=session_token,
            access_token=credentials.token or "",
            refresh_token=credentials.refresh_token,
            expires_at=credentials.expiry or (datetime.utcnow() + timedelta(hours=1)),
            created_at=datetime.utcnow()
        )
        
        # Store session
        self.sessions[session_token] = user_session
        
        return user_session
        
    async def authenticate_user_jwt(self, jwt_token: str) -> Dict[str, str]:
        """
        validate Google JWT and return OAuth URL for Gmail access
        - for users who signed in with Google but need Gmail permissions
        """
        try:
            # Verify the JWT token with Google
            idinfo = id_token.verify_oauth2_token(
                jwt_token, 
                requests.Request(), 
                self.client_id
            )
            
            # JWT is valid, but we need OAuth for Gmail API access
            # return OAuth URL for user to authorize Gmail permissions
            oauth_data = self.get_oauth_url()
            oauth_data["user_email"] = idinfo['email']
            oauth_data["message"] = "Please authorize Gmail access"
            
            return oauth_data
            
        except ValueError as e:
            raise Exception(f"Invalid JWT token: {str(e)}")
    
    async def validate_session(self, session_token: str) -> UserSession:
        # validate session token and return user session
        session = self.sessions.get(session_token)
        if not session:
            raise Exception("Invalid session token")
        
        # check if session is expired
        if datetime.utcnow() > session.expires_at:
            # refresh token
            if session.refresh_token:
                try:
                    await self._refresh_access_token(session)
                except Exception:
                    del self.sessions[session_token]
                    raise Exception("Session expired and refresh failed")
            else:
                del self.sessions[session_token]
                raise Exception("Session expired")
        
        return session
    
    async def _refresh_access_token(self, session: UserSession):
        # refresh the access token using refresh token
        credentials = Credentials(
            token=session.access_token,
            refresh_token=session.refresh_token,
            id_token=None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )
        
        # refresh the credentials
        credentials.refresh(requests.Request())
        
        # update session with new token
        session.access_token = credentials.token
        session.expires_at = credentials.expiry or (datetime.utcnow() + timedelta(hours=1))
    
    def create_gmail_service(self, session: UserSession):
        # create Gmail service object for authenticated user
        credentials = Credentials(
            token=session.access_token,
            refresh_token=session.refresh_token,
            id_token=None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )
        
        return build('gmail', 'v1', credentials=credentials)
    
    async def logout_user(self, session_token: str) -> bool:
        # logout user and invalidate session
        if session_token in self.sessions:
            session = self.sessions[session_token]
            
            # revoke the access token
            try:
                revoke_url = f"https://oauth2.googleapis.com/revoke?token={session.access_token}"
                async with httpx.AsyncClient() as client:
                    await client.post(revoke_url)
            except Exception:
                pass  # continue even if revoke fails
            
            del self.sessions[session_token]
            return True
        return False
