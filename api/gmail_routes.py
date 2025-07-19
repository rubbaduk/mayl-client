from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
import os

# Add path to import modules from backend  
gmail_backend_path = '/Users/davindo/Desktop/Projects/gmail-api-automate/gmail-api-automate'
if gmail_backend_path not in sys.path:
    sys.path.append(gmail_backend_path)

from auth import AuthService
from models import EmailSearchRequest, EmailSearchResponse, ChatRequest, ChatResponse
from agent import GmailAgent

# Import Gmail functions
try:
    import gmail_interact # type: ignore
    print("successfully imported gmail_interact")
except ImportError as e:
    print(f"couldn't import gmail_interact: {e}")
    gmail_interact = None

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


@router.get("/messages")
async def get_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    label: str = "INBOX",  # INBOX, SENT, DRAFT, SPAM, TRASH, or custom label
    query: str = "",       # search query (e.g., "from:example@gmail.com")
    page_token: str = "",  # for pagination
    max_results: int = 50  # email list
):
    """
    Get messages for any label/folder - this replaces multiple endpoints
    Examples:
    - /messages?label=INBOX (inbox view)
    - /messages?label=SENT (sent view) 
    - /messages?label=UNREAD (unread view)
    - /messages?query=from:boss@company.com (search results)
    """
    try:
        session = await auth_service.validate_session(credentials.credentials)
        gmail_service = auth_service.create_gmail_service(session)
        
        # build Gmail query based on label and search
        gmail_query = query
        if label and label != "ALL":
            gmail_query = f"label:{label} {query}".strip()
        
        # check if gmail_interact is available
        if not gmail_interact:
            raise HTTPException(status_code=500, detail="Gmail backend not available")
            
        # get messages using existing function
        messages = gmail_interact.search_emails(
            gmail_service, 
            query=gmail_query,
            max_results=max_results
        )
        
        email_list = []
        for msg in messages:
            details = gmail_interact.get_email_message_details(gmail_service, msg['id'])
            email_list.append({
                'id': msg['id'],
                'threadId': msg.get('threadId', msg['id']),
                'subject': details['subject'],
                'sender': details['sender'],
                'date': details['date'],
                'snippet': details['snippet'],
                'isRead': 'UNREAD' not in msg.get('labelIds', []),
                'hasAttachments': details['has_attachments'],
                'labels': msg.get('labelIds', [])
            })
        
        return {
            "messages": email_list,
            "totalCount": len(email_list),
            "currentLabel": label,
            "query": query,
            "nextPageToken": None  # implement pagination later
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.get("/message/{message_id}")
async def get_message_details(
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # ALL DETAILS WHEN USER CLICKS ON EMAIL
    try:
        session = await auth_service.validate_session(credentials.credentials)
        gmail_service = auth_service.create_gmail_service(session)
        
        if not gmail_interact:
            raise HTTPException(status_code=500, detail="Gmail backend not available")
        
        details = gmail_interact.get_email_message_details(gmail_service, message_id)
        
        return {
            "id": message_id,
            "subject": details['subject'],
            "sender": details['sender'],
            "recipients": details.get('recipients', []),
            "date": details['date'],
            "body": details['body'],
            "attachments": details.get('attachments', []),
            "labels": details.get('labels', []),
            "isRead": details.get('isRead', True),
            "threadId": details.get('threadId', message_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")

@router.get("/user-data")
async def get_user_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    
    # CAPTURE ALL DATA NEEDED FOR UI INITIALIZATION
    try:
        session = await auth_service.validate_session(credentials.credentials)
        gmail_service = auth_service.create_gmail_service(session)
        
        if not gmail_interact:
            raise HTTPException(status_code=500, detail="Gmail backend not available")
        
        # get labels for sidebar
        labels = gmail_interact.list_labels(gmail_service)
        
        # get basic stats
        stats = gmail_interact.get_email_stats_summary(gmail_service)
        
        return {
            "user": {
                "email": session.user_info.email,
                "name": session.user_info.name,
                "picture": session.user_info.picture
            },
            "labels": [
                {
                    "id": label["id"], 
                    "name": label["name"],
                    "type": label.get("type", "user"),
                    "messagesTotal": label.get("messagesTotal", 0),
                    "messagesUnread": label.get("messagesUnread", 0)
                } 
                for label in labels
            ],
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user data: {str(e)}")

@router.post("/message/{message_id}/action")
async def message_action(
    message_id: str,
    action: dict,  # {"type": "trash|archive|markRead|addLabel", "value": "..."}
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Perform actions on messages - like Gmail's toolbar actions
    Examples:
    - {"type": "trash"} - move to trash
    - {"type": "archive"} - archive message  
    - {"type": "markRead", "value": true} - mark as read/unread
    - {"type": "addLabel", "value": "IMPORTANT"} - add label
    """
    try:
        session = await auth_service.validate_session(credentials.credentials)
        gmail_service = auth_service.create_gmail_service(session)
        
        if not gmail_interact:
            raise HTTPException(status_code=500, detail="Gmail backend not available")
        
        action_type = action.get("type")
        action_value = action.get("value")
        
        if action_type == "trash":
            gmail_interact.trash_email(gmail_service, 'me', message_id)
            return {"success": True, "action": "trashed"}
            
        elif action_type == "archive":
            # implement archive function
            return {"success": True, "action": "archived"}
            
        elif action_type == "markRead":
            # implement mark read/unread
            return {"success": True, "action": f"marked {'read' if action_value else 'unread'}"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action_type}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # AI ASSISTANT
    try:
        session = await auth_service.validate_session(credentials.credentials)
        gmail_service = auth_service.create_gmail_service(session)
        
        # create AI agent with user's Gmail service
        try:
            agent = GmailAgent(gmail_service)
            response = agent.chat(request.message)
            return ChatResponse(response=response)
        except Exception as agent_error:
            # fallback to simple response if agent fails
            response = f"Mayl: I received your message '{request.message}'. AI agent had an issue: {str(agent_error)}"
            return ChatResponse(response=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# export router
gmail_router = router
