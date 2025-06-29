import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google_api import create_service

def init_gmail_service(client_file, api_name='gmail', api_version='v1', scopes=['https://mail.google.com/']):
    return create_service(client_file, api_name, api_version, scopes)

def _extract_body(payload):
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

'''
Example Payload:

payload = {
    'mimeType': 'multipart/mixed',
    'parts': [
        {
            'mimeType': 'multipart/alternative',
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'size': 25,
                        'data': 'SGVsbG8gdXNlcixUaGlzIGlzIGEgdGVzdC4='
                    }
                },
                {
                    'mimeType': 'text/html',
                    'body': {
                        'size': 61,
                        'data': 'PGRpdj5IZWxsbyB1c2VyLCBib2R5IGlzIGEgdGVzdC48L2Rpdj4='
                    }
                }
            ]
        },
        {
            'mimeType': 'application/pdf',
            'filename': 'report.pdf',
            'body': {
                'attachmentId': 'ANGjdJ…'
            }
        }
    ]
}

'''

def get_email_messages(service, user_id='me', label_ids=None, folder_name='INBOX', max_results=5):
    messages = []
    # For pagination
    next_page_token = None

    if folder_name:
        label_results = service.users().labels().list(userId=user_id).execute()
        labels = label_results.get('labels', [])
        folder_label_id = next((label['id'] for label in labels if label['name'].lower() == folder_name.lower()), None)

        if folder_label_id:
            if label_ids:
                label_ids.append(folder_label_id)
            else:
                label_ids = [folder_label_id]
        
        else:
            raise ValueError(f"Folder '{folder_name}' not found")
    
    while True:
        result = service.users().messages().list(
            userId = user_id,
            labelIds = label_ids,
            # Can only fetch up to 500 messages per API call
            maxResults = min(500, max_results - len(messages)) if max_results else 500,
            pageToken = next_page_token
        ).execute()

        messages.extend(result.get('messages', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(messages) >= max_results):
            break
    
    return messages[:max_results] if max_results else messages


def get_email_message_details(service, msg_id):
    message = service.users().messages().get(userId = 'me', id=msg_id, format='full').execute()
    payload = message['payload']
    # headers containing important email metadata
    headers = payload.get('headers', [])

    subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
    if not subject:
        subject = message.get('subject', 'No subject')
    
    sender = next((header['value'] for header in headers if header['name'] == 'From'), 'No sender')
    recipients = next((header['value'] for header in headers if header['name'] == 'To'), 'No Recipients')
    snippet = message.get('snippet', 'No Snippet')
    has_attachments = any(part.get('filename') for part in payload.get('parts', []) if part.get('filename'))
    date = next((header['value'] for header in headers if header['name'] == 'Date'), 'No Date')
    star = message.get('labelIds', []).count('STARRED') > 0
    label = ', '.join(message.get('labelIds', []))

    body = _extract_body(payload)

    return {
        'subject': subject,
        'sender': sender,
        'recipients': recipients,
        'body': body,
        'snippet': snippet,
        'has_attachments': has_attachments,
        'date': date,
        'star': star,
        'label': label,
    }
    
    '''
    example message:
    
    {
        "id": "12345abcdef",
        "snippet": "Hello Mark, looking forward...",
        "labelIds": ["INBOX", "STARRED"],
        "payload": {
            "headers": [
            { "name": "Subject", "value": "Meeting Tomorrow" },
            { "name": "From",    "value": "alice@example.com" },
            { "name": "To",      "value": "bob@example.com; carol@example.com" },
            { "name": "Date",    "value": "Fri, 13 Jun 2025 09:00:00 +0800" }
            ],
            "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                "data": "SGVsbG8gTWFyaywgbG9va2luZyBmb3J3YXJkIGxhdmUu"
                }
            }
            // no attachment parts here
            ]
        }
    }

    example return of func:

    {
    'subject': 'Meeting Tomorrow',
    'sender': 'alice@example.com',
    'recipients': 'bob@example.com; carol@example.com',
    'body': 'Hello Mark, looking forward lave.',
    'snippet': 'Hello Mark, looking forward...',
    'has_attachments': False,
    'date': 'Fri, 13 Jun 2025 09:00:00 +0800',
    'star': True,
    'label': 'INBOX, STARRED'
    }
    '''

