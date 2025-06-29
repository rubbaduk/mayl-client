import os
from gmail_interact import get_email_messages, get_email_message_details, init_gmail_service

client_file = 'client_secret.json'
service = init_gmail_service(client_file)
messages = get_email_messages(service, max_results= 2)

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


# Make sure we're in /Users/[username]/Projects/gmail-api-automate/gmail-api-automate