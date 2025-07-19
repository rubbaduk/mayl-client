from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserInfo(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    google_id: str

class UserSession(BaseModel):
    user_info: UserInfo
    session_token: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    created_at: datetime

class GoogleAuthRequest(BaseModel):
    credential: str

class EmailSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class EmailSearchResponse(BaseModel):
    emails: list
    total_count: int
    query: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
