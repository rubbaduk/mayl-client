import os
import base64
import datetime
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GmailService:
    def __init__(self, session_data: dict, client_id: str, client_secret: str):
        """initialize gmail service with oauth session credentials"""
        self.credentials = Credentials(
            token=session_data["access_token"],
            refresh_token=session_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=session_data["scopes"]
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)

    
    def search_emails(self, query: str = '', max_results: int = 200, user_id: str = 'me') -> List[Dict]:
        """search for emails using gmail search query syntax"""
        messages = []
        next_page_token = None
        
        try:
            while True:
                result = self.service.users().messages().list(
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
            
        except Exception as e:
            print(f"error searching emails: {e}")
            return []

    def get_email_messages(self, user_id='me', label_ids=None, folder_name='INBOX', max_results=500):
        """get emails from specific folder/labels"""
        messages = []
        next_page_token = None

        if folder_name:
            label_results = self.service.users().labels().list(userId=user_id).execute()
            labels = label_results.get('labels', [])
            folder_label_id = next((label['id'] for label in labels if label['name'].lower() == folder_name.lower()), None)

            if folder_label_id:
                if label_ids:
                    label_ids.append(folder_label_id)
                else:
                    label_ids = [folder_label_id]
            else:
                raise ValueError(f"folder '{folder_name}' not found")
        
        try:
            while True:
                result = self.service.users().messages().list(
                    userId=user_id,
                    labelIds=label_ids,
                    maxResults=min(500, max_results - len(messages)) if max_results else 500,
                    pageToken=next_page_token
                ).execute()

                messages.extend(result.get('messages', []))
                next_page_token = result.get('nextPageToken')

                if not next_page_token or (max_results and len(messages) >= max_results):
                    break
            
            return messages[:max_results] if max_results else messages
            
        except Exception as e:
            print(f"error getting email messages: {e}")
            return []

    def get_email_details(self, message_id: str, user_id: str = 'me') -> Dict[str, Any]:
        """get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId=user_id,
                id=message_id,
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])

            # extract headers
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'no subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'unknown sender')
            recipients = next((h['value'] for h in headers if h['name'] == 'To'), 'unknown recipients')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'unknown date')
            
            # extract body
            body = self._extract_body(payload)
            
            # check for attachments
            has_attachments = False
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('filename'):
                        has_attachments = True
                        break
            
            # get labels and other metadata
            labels = message.get('labelIds', [])
            star = 'STARRED' in labels
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'recipients': recipients,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', ''),
                'has_attachments': has_attachments,
                'star': star,
                'labels': labels,
                'label': ', '.join(labels)
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

    
    def count_emails_today(self, user_id: str = 'me') -> int:
        """count emails received today"""
        try:
            today = datetime.date.today()
            query = f"after:{today.strftime('%Y/%m/%d')}"
            
            results = self.service.users().messages().list(
                userId=user_id,
                q=query
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
        except Exception as e:
            print(f"error counting today's emails: {e}")
            return 0

    def count_emails_this_week(self, user_id: str = 'me') -> int:
        """count emails received this week"""
        try:
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            query = f"after:{start_of_week.strftime('%Y/%m/%d')}"
            
            results = self.service.users().messages().list(
                userId=user_id,
                q=query
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
        except Exception as e:
            print(f"error counting this week's emails: {e}")
            return 0

    def count_emails_this_month(self, user_id: str = 'me') -> int:
        """count emails received this month"""
        try:
            today = datetime.date.today()
            start_of_month = today.replace(day=1)
            query = f"after:{start_of_month.strftime('%Y/%m/%d')}"
            
            results = self.service.users().messages().list(
                userId=user_id,
                q=query
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
        except Exception as e:
            print(f"error counting this month's emails: {e}")
            return 0

    def get_email_stats_summary(self, user_id: str = 'me') -> Dict[str, int]:
        """get comprehensive email statistics"""
        try:
            stats = {
                'today': self.count_emails_today(user_id),
                'this_week': self.count_emails_this_week(user_id),
                'this_month': self.count_emails_this_month(user_id),
                'unread': 0,
                'with_attachments': 0,
                'total': 0
            }
            
            # get unread count
            unread_results = self.service.users().messages().list(
                userId=user_id,
                q='is:unread'
            ).execute()
            stats['unread'] = unread_results.get('resultSizeEstimate', 0)
            
            # get emails with attachments
            attachment_results = self.service.users().messages().list(
                userId=user_id,
                q='has:attachment'
            ).execute()
            stats['with_attachments'] = attachment_results.get('resultSizeEstimate', 0)
            
            # get total count
            total_results = self.service.users().messages().list(userId=user_id).execute()
            stats['total'] = total_results.get('resultSizeEstimate', 0)
            
            return stats
            
        except Exception as e:
            print(f"error getting email stats: {e}")
            return {
                'today': 0,
                'this_week': 0,
                'this_month': 0,
                'unread': 0,
                'with_attachments': 0,
                'total': 0
            }

    
    def list_labels(self, user_id: str = 'me') -> List[Dict]:
        """get all gmail labels/folders"""
        try:
            results = self.service.users().labels().list(userId=user_id).execute()
            return results.get('labels', [])
        except Exception as e:
            print(f"error listing labels: {e}")
            return []

    def get_labels(self) -> List[Dict]:
        """alias for list_labels for compatibility"""
        return self.list_labels()

    def create_label(self, name: str, label_list_visibility: str = 'labelShow', 
                    message_list_visibility: str = 'show', user_id: str = 'me'):
        """create a new gmail label"""
        try:
            label = {
                'name': name,
                'labelListVisibility': label_list_visibility,
                'messageListVisibility': message_list_visibility
            }
            created_label = self.service.users().labels().create(userId=user_id, body=label).execute()
            return created_label
        except Exception as e:
            print(f"error creating label: {e}")
            return None

    def get_label_details(self, label_id: str, user_id: str = 'me'):
        """get details of a specific label"""
        try:
            return self.service.users().labels().get(userId=user_id, id=label_id).execute()
        except Exception as e:
            print(f"error getting label details: {e}")
            return None

    def delete_label(self, label_id: str, user_id: str = 'me'):
        """delete a label"""
        try:
            self.service.users().labels().delete(userId=user_id, id=label_id).execute()
            return True
        except Exception as e:
            print(f"error deleting label: {e}")
            return False

    def map_label_name_to_id(self, label_name: str, user_id: str = 'me'):
        """get label id from label name"""
        try:
            labels = self.list_labels(user_id)
            label = next((label for label in labels if label['name'] == label_name), None)
            return label['id'] if label else None
        except Exception as e:
            print(f"error mapping label name to id: {e}")
            return None

    
    def trash_email(self, message_id: str, user_id: str = 'me') -> bool:
        """move email to trash"""
        try:
            self.service.users().messages().trash(userId=user_id, id=message_id).execute()
            return True
        except Exception as e:
            print(f"error trashing email: {e}")
            return False

    def untrash_email(self, message_id: str, user_id: str = 'me') -> bool:
        """remove email from trash"""
        try:
            self.service.users().messages().untrash(userId=user_id, id=message_id).execute()
            return True
        except Exception as e:
            print(f"error untrashing email: {e}")
            return False

    def delete_email(self, message_id: str, user_id: str = 'me') -> bool:
        """permanently delete email"""
        try:
            self.service.users().messages().delete(userId=user_id, id=message_id).execute()
            return True
        except Exception as e:
            print(f"error deleting email: {e}")
            return False

    def modify_email_labels(self, message_id: str, add_labels: List[str] = None, 
                           remove_labels: List[str] = None, user_id: str = 'me'):
        """add or remove labels from an email"""
        try:
            def batch_labels(labels, batch_size=100):
                return [labels[i:i + batch_size] for i in range(0, len(labels), batch_size)]

            if add_labels:
                for batch in batch_labels(add_labels):
                    self.service.users().messages().modify(
                        userId=user_id,
                        id=message_id,
                        body={'addLabelIds': batch}
                    ).execute()

            if remove_labels:
                for batch in batch_labels(remove_labels):
                    self.service.users().messages().modify(
                        userId=user_id,
                        id=message_id,
                        body={'removeLabelIds': batch}
                    ).execute()
            
            return True
        except Exception as e:
            print(f"error modifying email labels: {e}")
            return False

    
    def send_email(self, to: str, subject: str, body: str, body_type: str = 'plain', 
                  attachment_paths: List[str] = None, user_id: str = 'me'):
        """send an email"""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            if body_type.lower() not in ['plain', 'html']:
                raise ValueError("body_type must be plain or html")

            message.attach(MIMEText(body, body_type.lower()))

            # handle attachments
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
                        raise FileNotFoundError(f"file not found - {attachment_path}")
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            sent_message = self.service.users().messages().send(
                userId=user_id,
                body={'raw': raw_message}
            ).execute()

            return sent_message
        except Exception as e:
            print(f"error sending email: {e}")
            return None

    
    def search_email_conversations(self, query: str, max_results: int = 5, user_id: str = 'me'):
        """search email conversations/threads"""
        conversations = []
        next_page_token = None

        try:
            while True:
                result = self.service.users().threads().list(
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
        except Exception as e:
            print(f"error searching conversations: {e}")
            return []

    def get_message_and_replies(self, message_id: str, user_id: str = 'me'):
        """get a message and all its replies in the thread"""
        try:
            # get thread id from message
            message = self.service.users().messages().get(
                userId=user_id,
                id=message_id,
                format='full'            
            ).execute()
            thread_id = message['threadId']

            # get the whole thread
            thread = self.service.users().threads().get(
                userId=user_id,
                id=thread_id,
                format='minimal'        
            ).execute()

            processed_messages = []
            for msg in thread.get('messages', []):
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'no subject')
                from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'unknown sender')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'unknown date')

                content = self._extract_body(msg.get('payload', {}))

                processed_messages.append({
                    'id': msg.get('id'),
                    'subject': subject,
                    'from': from_addr,
                    'date': date,
                    'body': content
                })

            return processed_messages
        except Exception as e:
            print(f"error getting message and replies: {e}")
            return []

    
    def batch_trash_emails(self, message_ids: List[str], user_id: str = 'me'):
        """trash multiple emails in batch"""
        try:
            batch = self.service.new_batch_http_request()
            for message_id in message_ids:
                batch.add(self.service.users().messages().trash(userId=user_id, id=message_id))
            batch.execute()
            return True
        except Exception as e:
            print(f"error batch trashing emails: {e}")
            return False

    def batch_untrash_emails(self, message_ids: List[str], user_id: str = 'me'):
        """untrash multiple emails in batch"""
        try:
            batch = self.service.new_batch_http_request()
            for message_id in message_ids:
                batch.add(self.service.users().messages().untrash(userId=user_id, id=message_id))
            batch.execute()
            return True
        except Exception as e:
            print(f"error batch untrashing emails: {e}")
            return False

    def empty_trash(self, user_id: str = 'me'):
        """empty the trash folder"""
        page_token = None
        total_deleted = 0

        try:
            while True:
                response = self.service.users().messages().list(
                    userId=user_id,
                    q='in:trash',
                    pageToken=page_token,
                    maxResults=500
                ).execute()

                messages = response.get('messages', [])
                if not messages:
                    break

                batch = self.service.new_batch_http_request()
                for message in messages:
                    batch.add(self.service.users().messages().delete(userId=user_id, id=message['id']))
                batch.execute()

                total_deleted += len(messages)
                page_token = response.get('nextPageToken')

                if not page_token:
                    break

            return total_deleted
        except Exception as e:
            print(f"error emptying trash: {e}")
            return 0
