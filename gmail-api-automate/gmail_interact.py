import os
import base64
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google_api import create_service
import datetime

'''
- Extracts Email Body
- Retrieves/Reads Email body
- Retrieves Email Details
- Send Email

'''

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

def get_email_messages(service, user_id='me', label_ids=None, folder_name='INBOX', max_results=500):
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
    Example message:
    
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

def send_email(service, to, subject, body, body_type = 'plain', attachment_paths = None):
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject

    if body_type.lower() not in ['plain', 'html']:
        raise ValueError("body_type must be plain or html")

    message.attach(MIMEText(body, body_type.lower()))

    # HANDLING EMAIL ATTACHMENTS

    if attachment_paths:
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)

                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{filename}\"",
                )

                message.attach(part)
            
            else:
                raise FileNotFoundError(f"File not found - {attachment_path}")
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    sent_message = service.users().messages().send(
        userId='me',
        body={'raw': raw_message}
    ).execute()

    return sent_message


def download_attachments_main(service, user_id, msg_id, target_dir):
    
    os.makedirs(target_dir, exist_ok=True)

    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    for part in message['payload']['parts']:
        if part['filename']:
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
            data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            file_path = os.path.join(target_dir, part['filename'])
            print('Attachment is saving to: ', file_path)
            with open(file_path, 'wb') as f:
                f.write(file_data)

# Get attachments of entire thread
def download_attachments_all(service, user_id, msg_id, target_dir):
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    thread = service.users().threads().get(userId=user_id, id=msg_id).execute()
    for message in thread['messages']:
        for part in message['payload']['parts']:
            if part['filename']:
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
                data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                file_path = os.path.join(target_dir, part['filename'])
                print('Attachment is saving to: ', file_path)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
    


# Search Functions - returns message objects that match queries
'''
https://developers.google.com/workspace/gmail/api/guides/filtering
https://support.google.com/mail/answer/7190

'''

def search_emails(service, query, user_id='me', max_results=200):
    """
    example queries:
        - "from:example@gmail.com" - emails from specific sender
        - "subject:meeting" - emails with "meeting" in subject
        - "has:attachment" - emails with attachments
        - "is:unread" - unread emails
        - "label:inbox" - emails in inbox
        - "after:2024/01/01" - emails after specific date
        - "before:2024/12/31" - emails before specific date
    """

    messages = []
    next_page_token = None
    
    while True:
        result = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(messages)) if max_results else 500,
            pageToken=next_page_token
        ).execute()
        
        messages.extend(result.get('messages', []))
        
        next_page_token = result.get('nextPageToken')
        
        if not next_page_token or (max_results and len(messages) >= max_results):
            break
    
    return messages[:max_results] if max_results else messages


def search_email_conversation(service, query, user_id='me', max_results=5):
    conversations = []
    next_page_token = None

    while True:
        result = service.users().threads().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(conversations)) if max_results else 500,
            pageToken=next_page_token
        ).execute()
        
        conversations.extend(result.get('threads', []))
        
        next_page_token = result.get('nextPageToken')
        
        if not next_page_token or (max_results and len(conversations) >= max_results):
            break
    
    return conversations[:max_results] if max_results else conversations


# Label Handling

def create_label(service, name, label_list_visibility = 'labelShow', message_list_visibility = 'show'):
    label = {
        'name':name,
        # controls visibility of gmail label
        'labelListVisibility':label_list_visibility,
        # checks to see if the label is showing in email message
        'messageListVisibility': message_list_visibility
    }
    created_label = service.users().labels().create(userId='me', body=label).execute()
    return created_label

def list_labels(service):
    results = service.users().labels().list(userId = 'me').execute()
    labels = results.get('labels', [])
    return labels

def get_label_details(service, label_id):
    return service.users().labels().get(userId='me', id=label_id).execute()

def modify_label(service, label_id, **updates):
    label = service.users().labels().get(userId='me', id=label_id).execute()
    for key, value in updates.items():
        label[key] = value
    
    updated_label = service.users().labels().update(userId='me', id=label_id, body=label).execute()
    return updated_label

def delete_label(service, label_id):
    service.users().labels().delete(userId='me', id=label_id).execute()

def map_label_name_to_id(service, label_name):
    labels = list_labels(service)
    label = next((label for label in labels if label['name'] == label_name), None)
    return label['id'] if label else None

# Manages labels from emails:

def modify_email_labels(service, user_id, message_id, add_labels = None, remove_labels = None):
    
    # Sorts list of labels into batches
    def batch_labels(labels, batch_size = 100):
        return [labels[i:i + batch_size] for i in range(0, len(labels), batch_size)]

    if add_labels:
        for batch in batch_labels(add_labels):
            service.users().messages().modify(
                userId=user_id,
                id=message_id,
                body={'addLabelIds': batch}
            ).execute()

    if remove_labels:
        for batch in batch_labels(remove_labels):
            service.users().messages().modify(
            userId=user_id,
            id=message_id,
            body={'removeLabelIds': batch}
    ).execute()


# Trash/Delete Emails

def trash_email(service, user_id, message_id):
    service.users().messages().trash(userId=user_id, id=message_id).execute()


def batch_trash_emails(service, user_id, message_ids):
    # combine multiple API calls into a single request
    batch = service.new_batch_http_request()
    for message_id in message_ids:
        batch.add(service.users().messages().trash(userId=user_id, id=message_id))
    batch.execute()

def perm_delete_email(service, user_id, message_id):
    service.users().message().delete(userId=user_id, id=message_id).execute()


# UNDO TRASH EMAILS

def untrash_email(service, user_id, message_id):
    service.users().messages().untrash(userId=user_id, id=message_id).execute()


def batch_untrash_emails(service, user_id, message_ids):
    # combine multiple API calls into a single request
    batch = service.new_batch_http_request()
    for message_id in message_ids:
        batch.add(service.users().messages().untrash(userId=user_id, id=message_id))
    batch.execute()


def empty_trash(service):
    page_token = None
    total_deleted = 0

    while True:
        response = service.users().messages().list(
            userId = 'me',
            q = 'in:trash',
            pageToken = page_token,
            maxResults = 500
        ).execute()

        messages = response.get('messages', [])
        if not messages:
            break

        batch = service.new_batch_http_request()
        for message in messages:
            batch.add(service.users().messages().delete(userId='me', id=message['id']))
        batch.execute()

        total_deleted += len(messages)

        page_token = response.get('nextPageToken')

        if not page_token:
            break

    return total_deleted


def list_draft_emails(service, user_id='me', max_results=100):
    drafts = []
    next_page_token = None

    while True:
        result = service.users().drafts().list(
            userId = user_id,
            maxResults=min(500, max_results - len(drafts)) if max_results else 500,
            pageToken = next_page_token
        ).execute()

        drafts.extend(result.get('drafts', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(drafts) >= max_results):
            break
    
    return drafts[:max_results] if max_results else drafts


def create_draft_email(service, to, subject, body, body_type='plain', attachment_paths=None):
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject

    if body_type.lower() not in ['plain', 'html']:
        raise ValueError("body_type must be either 'plain' or 'html'")

    message.attach(MIMEText(body, body_type.lower()))

    if attachment_paths:
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)

                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )

                message.attach(part)
            else:
                raise FileNotFoundError(f"File not found - {attachment_path}")

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    draft = service.users().drafts().create(
        userId='me',
        body={'message': {'raw': raw_message}}
    ).execute()

    return draft




def get_draft_email_message_details(service, draft_id, format='full'):

    draft_detail = service.users().drafts().get(
        userId='me',
        id=draft_id,
        format=format
    ).execute()

    # pull out the message and its payload
    draft_message = draft_detail['message']
    draft_payload = draft_message['payload']
    headers = draft_payload.get('headers', [])


    subject    = next((h['value'] for h in headers if h['name'] == 'Subject'),    'No subject')
    sender     = next((h['value'] for h in headers if h['name'] == 'From'),       'No sender')
    recipients = next((h['value'] for h in headers if h['name'] == 'To'),         'No recipients')
    date       = next((h['value'] for h in headers if h['name'] == 'Date'),       'No date')
    snippet    = draft_message.get('snippet',                                   'No snippet')
    labels     = draft_message.get('labelIds', [])

    # flags
    has_attachments = any(
        part.get('filename')
        for part in draft_payload.get('parts', [])
        if part.get('filename')
    )
    star = 'STARRED' in labels
    label = ', '.join(labels)

    body = '<Text body not available>'

    # look for a plain-text part
    if 'parts' in draft_payload:
        for part in draft_payload['parts']:
            # multipart/alternative may contain text/plain sub-parts
            if part['mimeType'] == 'multipart/alternative':
                for subpart in part.get('parts', []):
                    if subpart['mimeType'] == 'text/plain' and 'data' in subpart.get('body', {}):
                        data = subpart['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            # direct text/plain part
            elif part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break

    return {
        'subject':       subject,
        'sender':        sender,
        'recipients':    recipients,
        'body':          body,
        'snippet':       snippet,
        'has_attachments': has_attachments,
        'date':          date,
        'star':          star,
        'label':         label
    }


def send_draft_email(service, draft_id):
    draft = service.users().drafts().send(userId = 'me', body={'id': draft_id}).execute()
    return draft

def delete_draft_email(service, draft_id):
    service.users().drafts().delete(userId='me', id=draft_id).execute()


def get_message_and_replies(service, message_id):
    # grab thread id
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'            
    ).execute()
    thread_id = message['threadId']

    # pull the whole thread
    thread = service.users().threads().get(
        userId='me',
        id=thread_id,
        format='minimal'        
    ).execute()

    processed_messages = []
    for msg in thread.get('messages', []):
        headers = msg.get('payload', {}).get('headers', [])
        subject    = next((h['value'] for h in headers if h['name'].lower() == 'subject'),    'No Subject')
        from_addr  = next((h['value'] for h in headers if h['name'].lower() == 'from'),       'Unknown Sender')
        date       = next((h['value'] for h in headers if h['name'].lower() == 'date'),       'Unknown Date')

        # assumes you have a helper that walks the payload and returns the decoded text
        content = _extract_body(msg.get('payload', {}))

        processed_messages.append({
            'id':      msg.get('id'),
            'subject': subject,
            'from':    from_addr,
            'date':    date,
            'body':    content
        })

    return processed_messages


# RETRIEVE EMAIL NUMBERS

def get_current_month_date_range():
    """Get start and end dates for current month in Gmail search format"""
    now = datetime.datetime.now()
    start_of_month = now.replace(day=1)
    
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    
    # Format for Gmail search (YYYY/MM/DD)
    start_date = start_of_month.strftime('%Y/%m/%d')
    end_date = next_month.strftime('%Y/%m/%d')
    
    return start_date, end_date

def count_emails_by_date_range(service, start_date=None, end_date=None, additional_query=""):
    
    date_query = ""
    if start_date:
        date_query += f"after:{start_date} "
    if end_date:
        date_query += f"before:{end_date} "
    
    full_query = f"{date_query}{additional_query}".strip()
    
    # use search to get count 
    try:
        result = service.users().messages().list(
            userId='me',
            q=full_query,
            maxResults=1  #only need to know if there are results
        ).execute()
        
        if 'messages' not in result:
            return 0
        
        total_count = 0
        next_page_token = None
        
        while True:
            result = service.users().messages().list(
                userId='me',
                q=full_query,
                maxResults=500,  
                pageToken=next_page_token
            ).execute()
            
            messages = result.get('messages', [])
            total_count += len(messages)
            
            next_page_token = result.get('nextPageToken')
            if not next_page_token:
                break
        
        return total_count
        
    except Exception as e:
        print(f"Error counting emails: {e}")
        return 0

def count_emails_this_month(service):
    start_date, end_date = get_current_month_date_range()
    return count_emails_by_date_range(service, start_date, end_date)

def count_emails_this_week(service):
    now = datetime.datetime.now()
    start_of_week = now - datetime.timedelta(days=now.weekday())
    start_date = start_of_week.strftime('%Y/%m/%d')
    
    return count_emails_by_date_range(service, start_date, None)

def count_emails_today(service):
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    return count_emails_by_date_range(service, today, None)

def get_email_stats_summary(service):
    
    stats = {
        'today': count_emails_today(service),
        'this_week': count_emails_this_week(service),
        'this_month': count_emails_this_month(service),
        'unread': count_emails_by_date_range(service, additional_query="is:unread"),
        'with_attachments': count_emails_by_date_range(service, additional_query="has:attachment"),
    }
    
    return stats


