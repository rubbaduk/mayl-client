"""
Gmail interaction functions for FastAPI backend
simplified version of the main gmail_interact.py
"""
import base64
import datetime
from typing import List, Dict, Any

def extract_body(payload):
    body = '<Text body not available>'

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

def search_emails(service, query: str = '', max_results: int = 10) -> List[Dict]:
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        return messages
    except Exception as e:
        print(f"An error occurred in search_emails: {e}")
        return []

def get_email_message_details(service, message_id: str) -> Dict[str, Any]:
    # get info about certain email
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        payload = message['payload']
        headers = payload.get('headers', [])
        
        # extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        recipients = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipients')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        body = extract_body(payload)
        
        has_attachments = False
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    has_attachments = True
                    break
        
        labels = message.get('labelIds', [])
        
        return {
            'id': message_id,
            'subject': subject,
            'sender': sender,
            'recipients': recipients,
            'date': date,
            'body': body,
            'snippet': message.get('snippet', ''),
            'has_attachments': has_attachments,
            'label': labels
        }
        
    except Exception as e:
        print(f"An error occurred in get_email_message_details: {e}")
        return {}

def list_labels(service) -> List[Dict]:
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return labels
    except Exception as e:
        print(f"An error occurred in list_labels: {e}")
        return []

def trash_email(service, user_id: str, message_id: str) -> bool:
    try:
        service.users().messages().trash(
            userId=user_id,
            id=message_id
        ).execute()
        return True
    except Exception as e:
        print(f"An error occurred in trash_email: {e}")
        return False

def count_emails_today(service) -> int:
    try:
        today = datetime.date.today()
        query = f"after:{today.strftime('%Y/%m/%d')}"
        
        results = service.users().messages().list(
            userId='me',
            q=query
        ).execute()
        
        return results.get('resultSizeEstimate', 0)
    except Exception as e:
        print(f"An error occurred in count_emails_today: {e}")
        return 0

def count_emails_this_week(service) -> int:
    try:
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        query = f"after:{start_of_week.strftime('%Y/%m/%d')}"
        
        results = service.users().messages().list(
            userId='me',
            q=query
        ).execute()
        
        return results.get('resultSizeEstimate', 0)
    except Exception as e:
        print(f"An error occurred in count_emails_this_week: {e}")
        return 0

def count_emails_this_month(service) -> int:
    try:
        today = datetime.date.today()
        start_of_month = today.replace(day=1)
        query = f"after:{start_of_month.strftime('%Y/%m/%d')}"
        
        results = service.users().messages().list(
            userId='me',
            q=query
        ).execute()
        
        return results.get('resultSizeEstimate', 0)
    except Exception as e:
        print(f"An error occurred in count_emails_this_month: {e}")
        return 0

def get_email_stats_summary(service) -> Dict[str, int]:
    try:
        stats = {
            'today': count_emails_today(service),
            'this_week': count_emails_this_week(service),
            'this_month': count_emails_this_month(service),
            'unread': 0,
            'with_attachments': 0,
            'total': 0
        }
        
        # Get unread count
        unread_results = service.users().messages().list(
            userId='me',
            q='is:unread'
        ).execute()
        stats['unread'] = unread_results.get('resultSizeEstimate', 0)
        
        # Get emails with attachments
        attachment_results = service.users().messages().list(
            userId='me',
            q='has:attachment'
        ).execute()
        stats['with_attachments'] = attachment_results.get('resultSizeEstimate', 0)
        
        # Get total count
        total_results = service.users().messages().list(userId='me').execute()
        stats['total'] = total_results.get('resultSizeEstimate', 0)
        
        return stats
        
    except Exception as e:
        print(f"An error occurred in get_email_stats_summary: {e}")
        return {
            'today': 0,
            'this_week': 0,
            'this_month': 0,
            'unread': 0,
            'with_attachments': 0,
            'total': 0
        }
