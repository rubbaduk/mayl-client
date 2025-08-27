import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, SystemMessage
from .gmail_service import GmailService

load_dotenv()

# global gmail service reference for tools
_gmail_service = None

def init_gmail_service(service):
    """initialize gmail service for tools"""
    global _gmail_service
    _gmail_service = service

@tool
def search_emails_tool(query: str, max_results: int = 5) -> str:
    """search for emails using gmail search query syntax"""
    if not _gmail_service:
        return "gmail service not initialized"
    
    try:
        messages = _gmail_service.search_emails(query, max_results)
        if not messages:
            return f"no emails found matching query: {query}"
        
        results = []
        for msg in messages[:max_results]:
            details = _gmail_service.get_email_details(msg['id'])
            if details:
                results.append(f"id: {msg['id']}, subject: {details['subject']}, from: {details['sender']}, date: {details['date']}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"error searching emails: {str(e)}"

@tool
def get_email_details_tool(message_id: str) -> str:
    """get detailed information about a specific email"""
    if not _gmail_service:
        return "gmail service not initialized"
    
    try:
        details = _gmail_service.get_email_details(message_id)
        if not details:
            return f"email not found: {message_id}"
        
        return f"subject: {details['subject']}\nfrom: {details['sender']}\ndate: {details['date']}\nbody: {details['body'][:500]}..."
        
    except Exception as e:
        return f"error getting email details: {str(e)}"

@tool
def list_labels_tool() -> str:
    """list available gmail labels/folders"""
    if not _gmail_service:
        return "gmail service not initialized"
    
    try:
        labels = _gmail_service.list_labels()
        label_names = [label['name'] for label in labels]
        return f"available labels: {', '.join(label_names)}"
        
    except Exception as e:
        return f"error getting labels: {str(e)}"

@tool
def trash_email_tool(message_id: str) -> str:
    """move an email to trash"""
    if not _gmail_service:
        return "gmail service not initialized"
    
    try:
        success = _gmail_service.trash_email(message_id)
        if success:
            return f"email {message_id} moved to trash"
        else:
            return f"failed to trash email {message_id}"
            
    except Exception as e:
        return f"error trashing email: {str(e)}"

@tool
def get_email_stats_tool() -> str:
    """get comprehensive email statistics"""
    if not _gmail_service:
        return "gmail service not initialized"
    
    try:
        stats = _gmail_service.get_email_stats_summary()
        return f"""Email Statistics:
Total emails: {stats['total']}
Unread emails: {stats['unread']}
Emails today: {stats['today']}
Emails this week: {stats['this_week']}
Emails this month: {stats['this_month']}
With attachments: {stats['with_attachments']}"""
        
    except Exception as e:
        return f"error getting email stats: {str(e)}"

class MailAgent:
    def __init__(self, gmail_service):
        # initialize gmail service for tools
        init_gmail_service(gmail_service)
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.tools = [
            search_emails_tool,
            get_email_details_tool,
            list_labels_tool,
            trash_email_tool,
            get_email_stats_tool
        ]
        self.agent_executor = self._create_agent()
    
    def _create_agent(self):
        """create the langchain agent with gmail tools"""
        system_prompt = """you are a helpful gmail assistant. you can help users manage their emails using the available tools.

        key capabilities:
        - search for emails using gmail search syntax
        - view email details
        - list available labels/folders  
        - move emails to trash (with user confirmation)

        important guidelines:
        - always confirm before performing destructive actions like deleting emails
        - use gmail search syntax for queries (e.g., 'from:sender@email.com', 'subject:keyword', 'is:unread')
        - provide clear, helpful responses about what you found or did
        - if a user asks to delete emails, first search and show what would be deleted, then ask for confirmation

        gmail search syntax examples:
        - from:john@example.com (emails from specific sender)
        - subject:meeting (emails with "meeting" in subject)
        - is:unread (unread emails)
        - has:attachment (emails with attachments)
        - after:2024/01/01 (emails after specific date)
        - category:promotions (promotional emails)
        """
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt_template
        )
        
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            max_iterations=3
        )
    
    def chat(self, user_input: str) -> str:
        """process user input and return response"""
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result["output"]
        except Exception as e:
            return f"sorry, i encountered an error: {str(e)}"