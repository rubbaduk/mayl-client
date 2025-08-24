from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import AuthService
from .gmail_service import GmailService

router = APIRouter(prefix="/gmail", tags=["gmail"])
security = HTTPBearer()

@router.get("/messages")
async def get_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    query: str = "",
    max_results: int = 50
):
    """get gmail messages using fastapi auth"""
    try:
        # create auth service instance here instead
        auth_service = AuthService()
        
        # validate session and get credentials
        session_data = await auth_service.validate_session(credentials.credentials)
        
        # create gmail service with session credentials
        gmail_service = GmailService(
            session_data, 
            auth_service.client_id, 
            auth_service.client_secret
        )
        
        # search emails
        messages = gmail_service.search_emails(query, max_results)
        
        # get details for each message
        detailed_messages = []
        for msg in messages[:10]:  # limit details to first 10
            details = gmail_service.get_email_details(msg['id'])
            if details:
                detailed_messages.append(details)
        
        return {
            "messages": detailed_messages,
            "total_count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(500, f"error fetching messages: {str(e)}")

@router.get("/message/{message_id}")
async def get_message(
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """get specific email details"""
    try:
        auth_service = AuthService()
        session_data = await auth_service.validate_session(credentials.credentials)
        gmail_service = GmailService(
            session_data, 
            auth_service.client_id, 
            auth_service.client_secret
        )
        
        details = gmail_service.get_email_details(message_id)
        if not details:
            raise HTTPException(404, "message not found")
        
        return details
        
    except Exception as e:
        raise HTTPException(500, f"error fetching message: {str(e)}")

@router.post("/chat")
async def gmail_chat(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """ai chat interface for gmail management"""
    try:
        auth_service = AuthService()
        session_data = await auth_service.validate_session(credentials.credentials)
        gmail_service = GmailService(
            session_data,
            auth_service.client_id, 
            auth_service.client_secret
        )
        
        # create agent with gmail service
        from .agent_fastapi import MailAgent
        agent = MailAgent(gmail_service)
        
        # process user message
        user_message = request.get("message", "")
        response = agent.chat(user_message)
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(500, f"error in chat: {str(e)}")
