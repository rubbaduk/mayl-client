import os
from pathlib import Path
from gmail_interact import get_email_messages, get_email_message_details, init_gmail_service
from gmail_interact import send_email
from gmail_interact import download_attachments_all, download_attachments_main
from gmail_interact import search_emails, search_email_conversation

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

to_address = 'cheesyspotato@gmail.com'
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

# TEST DOWNLOADING ATTACHMENTS

user_id = 'me'
msg_id = '197bab7f175c7da1'
thread_id = '197bab7f175c7da1'
download_dir = Path('./downloads')

download_attachments_main(service, user_id, msg_id, download_dir)

# TEST SEARCHING FUNCTIONS

# Test 1: Search for emails from a specific sender
print("\n" + "="*60)
print("TEST 1: Searching for emails from Gmail team")
print("="*60)

search_query1 = "from:gmail-noreply@google.com"
search_results1 = search_emails(service, search_query1, max_results=3)

print(f"Found {len(search_results1)} emails from Gmail team:")
for msg in search_results1:
    details = get_email_message_details(service, msg['id'])
    print(f"  - Subject: {details['subject']}")
    print(f"    From: {details['sender']}")
    print(f"    Date: {details['date']}")
    print()

# Test 2: Search for emails with attachments
print("\n" + "="*60)
print("TEST 2: Searching for emails with attachments")
print("="*60)

search_query2 = "has:attachment"
search_results2 = search_emails(service, search_query2, max_results=2)

print(f"Found {len(search_results2)} emails with attachments:")
for msg in search_results2:
    details = get_email_message_details(service, msg['id'])
    print(f"  - Subject: {details['subject']}")
    print(f"    From: {details['sender']}")
    print(f"    Has Attachments: {details['has_attachments']}")
    print()

# Test 3: Search for unread emails
print("\n" + "="*60)
print("TEST 3: Searching for unread emails")
print("="*60)

search_query3 = "is:unread"
search_results3 = search_emails(service, search_query3, max_results=5)

print(f"Found {len(search_results3)} unread emails:")
for msg in search_results3:
    details = get_email_message_details(service, msg['id'])
    print(f"  - Subject: {details['subject']}")
    print(f"    From: {details['sender']}")
    print(f"    Snippet: {details['snippet'][:50]}...")
    print()

# Test 4: Search email conversations/threads
print("\n" + "="*60)
print("TEST 4: Searching for email conversations")
print("="*60)

# Use a thread_id from your recent emails
if search_results1:  # If we found any emails from previous search
    sample_thread_id = search_results1[0]['threadId']
    conversation = search_email_conversation(service, sample_thread_id)
    
    if conversation:
        print(f"Conversation Details:")
        print(f"  Thread ID: {conversation['thread_id']}")
        print(f"  Message Count: {conversation['message_count']}")
        print(f"  Messages in conversation:")
        
        for i, msg in enumerate(conversation['messages'], 1):
            print(f"    Message {i}:")
            print(f"      Subject: {msg['subject']}")
            print(f"      From: {msg['sender']}")
            print(f"      Snippet: {msg['snippet'][:50]}...")
            print()
else:
    print("No emails found to test conversation search")

print("\n" + "="*60)
print("SEARCH TESTS COMPLETED")
print("="*60)