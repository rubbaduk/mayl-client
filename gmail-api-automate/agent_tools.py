from langchain_core.tools import tool
import gmail_interact


service = None

def init_gmail_service(gmail_service):
    global service
    if gmail_service is None:
        print("Failed to initialize gmail service")
        return False
    
    service = gmail_service
    return True

@tool
def search_emails_tool(query: str, max_results: int = 5) -> str:
    try:
        if service is None:
            return "Error: gmail service not initialized. Call init_gmail_service() first."
        messages = gmail_interact.search_emails(
            service, 
            query=query, 
            max_results=max_results
        )
        
        if not messages:
            return f"No emails found matching query: {query}"
        
        results = []
        for msg in messages:
            details = gmail_interact.get_email_message_details(service, msg['id'])
            results.append({
                'id': msg['id'],
                'subject': details['subject'],
                'sender': details['sender'],
                'date': details['date'],
                'snippet': details['snippet']
            })
        
        return f"Found {len(results)} emails:\n" + "\n".join([
            f"- {email['subject']} from {email['sender']} ({email['date']})"
            for email in results
        ])
        
    except Exception as e:
        return f"Error searching emails: {str(e)}"

@tool
def get_email_details_tool(message_id: str) -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        details = gmail_interact.get_email_message_details(service, message_id)
        return f"""
                Email Details:
                Subject: {details['subject']}
                From: {details['sender']}
                To: {details['recipients']}
                Date: {details['date']}
                Has Attachments: {details['has_attachments']}
                Labels: {details['label']}

                Body Preview:
                {details['body'][:500]}...
                """
    except Exception as e:
        return f"Error getting email details: {str(e)}"

@tool
def list_labels_tool() -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        labels = gmail_interact.list_labels(service)
        label_names = [label['name'] for label in labels]
        return f"Available labels: {', '.join(label_names)}"
    except Exception as e:
        return f"Error listing labels: {str(e)}"

@tool
def trash_email_tool(message_id: str) -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        gmail_interact.trash_email(service, 'me', message_id)
        return f"Successfully moved email {message_id} to trash"
    except Exception as e:
        return f"Error trashing email: {str(e)}"

@tool
def count_emails_this_month_tool() -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        count = gmail_interact.count_emails_this_month(service)
        return f"You have received {count} emails this month."
    except Exception as e:
        return f"Error counting emails this month: {str(e)}"

@tool
def count_emails_this_week_tool() -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        count = gmail_interact.count_emails_this_week(service)
        return f"You have received {count} emails this week."
    except Exception as e:
        return f"Error counting emails this week: {str(e)}"

@tool
def count_emails_today_tool() -> str:
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        count = gmail_interact.count_emails_today(service)
        return f"You have received {count} emails today."
    except Exception as e:
        return f"Error counting emails today: {str(e)}"

@tool
def get_email_stats_tool() -> str:
    """Get comprehensive email statistics including counts for today, this week, this month, unread emails, and emails with attachments"""
    try:
        if service is None:
            return "Error: Gmail service not initialized. Call init_gmail_service() first."
        stats = gmail_interact.get_email_stats_summary(service)
        return f"""Email Statistics:
            - Today: {stats['today']} emails
            - This week: {stats['this_week']} emails  
            - This month: {stats['this_month']} emails
            - Unread: {stats['unread']} emails
            - With attachments: {stats['with_attachments']} emails
            - Total emails: {stats['total']} emails"""
    except Exception as e:
        return f"Error getting email stats: {str(e)}"
