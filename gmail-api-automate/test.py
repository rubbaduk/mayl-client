import os
from pathlib import Path
from gmail_interact import get_email_messages, get_email_message_details, init_gmail_service
from gmail_interact import send_email

client_file = 'client_secret.json'
service = init_gmail_service(client_file)
messages = get_email_messages(service, max_results= 2)

# Make sure we're in /Users/[username]/Projects/gmail-api-automate/gmail-api-automate

# TEST READING EMAILS

print(messages)
'''
"id" - unique identifier for individual messages
"threadId" - identifies conversations; back and forth emails -> one to many relationship
'''

for msg in messages:
    details = get_email_message_details(service, msg['id'])
    if details:
        print(f"Subject: {details['subject']}")
        print(f"From: {details['sender']}")
        print(f"To: {details['recipients']}")
        print(f"Date: {details['date']}")
        print(f"Starred: {details['star']}")
        print(f"Labels: {details['label']}")
        print(f"Has Attachments: {details['has_attachments']}")
        print(f"Snippet: {details['snippet']}")
        print(f"Body: {details['body']}")
        print("-" * 50) 


# TEST SENDING EMAILS

to_address = 'TEST3124112353@gmail.com'
email_subject = 'Gmail API Sending Email Test'
email_body = 'This is a test using Gmails API'

attachment_dir = Path('./attachments')
attachment_files = list(attachment_dir.glob('*'))

sent_email = send_email(
    service,
    to_address,
    email_subject,
    email_body,
    body_type='plain',
    attachment_paths=attachment_files
)

print(sent_email)