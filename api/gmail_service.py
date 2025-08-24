from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from typing import List, Dict, Any
from datetime import datetime

class GmailService:
    def __init__(self, session_data: dict, client_id: str, client_secret: str):
        """initialize gmail service with session credentials"""
        self.credentials = Credentials(
            token=session_data["access_token"],
            refresh_token=session_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=session_data["scopes"]
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    def search_emails(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """search emails using gmail api"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return messages
            
        except Exception as e:
            print(f"error searching emails: {e}")
            return []
    
    def get_email_details(self, message_id: str) -> Dict:
        """get detailed email information"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # extract email details
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'no subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'unknown sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'unknown date')
            
            # extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
            
        except Exception as e:
            print(f"error getting email details: {e}")
            return {}
    
    def _extract_body(self, payload):
        """extract email body from payload"""
        body = 'text body not available'

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'multipart/alternative':
                    for subpart in part['parts']:
                        if subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']:
                            body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                            break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body
    
    def get_labels(self) -> List[Dict]:
        """get gmail labels/folders"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            return results.get('labels', [])
        except Exception as e:
            print(f"error getting labels: {e}")
            return []
    
    def trash_email(self, message_id: str) -> bool:
        """move email to trash"""
        try:
            self.service.users().messages().trash(userId='me', id=message_id).execute()
            return True
        except Exception as e:
            print(f"error trashing email: {e}")
            return False