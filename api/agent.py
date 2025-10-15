import os
import sys
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

# NOTE: functions are dynamically imported - will trigger linter

# Add path to import gmail_interact from backend
gmail_backend_path = '/Users/davindo/Desktop/Projects/gmail-api-automate/gmail-api-automate'
if gmail_backend_path not in sys.path:
    sys.path.append(gmail_backend_path)

# Import Gmail functions directly
try:
    import gmail_interact # type: ignore
    print("Gmail interact imported successfully in agent.py")
except ImportError as e:
    print(f"couldn't import gmail_interact in agent.py: {e}")
    gmail_interact = None

class GmailAgent:
    def __init__(self, gmail_service):
        # initialize the Gmail AI agent with a user's Gmail service
        self.gmail_service = gmail_service
        
        if not gmail_interact:
            raise ValueError("Gmail interact module not available")
        
        # Initialize OpenAI model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # create tools that use the gmail_service directly
        self.tools = self._create_tools()
        
        # create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a helpful Gmail assistant that can help users manage their emails using natural language.

            You have access to tools that allow you to:
            - Search for emails using queries
            - Get detailed information about specific emails
            - View available labels
            - Move emails to trash
            - Get email statistics (today, this week, this month, unread count, etc.)

            When a user asks about emails, try to understand their intent and use the appropriate tools to help them.

            Some example interactions:
            - "How many emails did I get today?" → Use count_emails_today
            - "Find emails from John" → Use search_emails with query "from:john"
            - "Show me my email stats" → Use get_email_stats
            - "Delete email with ID 123" → Use trash_email with the ID

            Always be helpful, clear, and explain what actions you're taking. 
            If you can't do the task or don't fully understand what the user is asking, 
            Reply with 'I'm sorry, I can't do that'"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def _create_tools(self):
        """Create LangChain tools that use the gmail_service"""
        
        @tool
        def search_emails(query: str, max_results: int = 5) -> str:
            """Search for emails using Gmail search query syntax. 
            Examples: 'from:john@example.com', 'subject:meeting', 'is:unread'"""
            try:
                messages = gmail_interact.search_emails(
                    self.gmail_service, 
                    query=query, 
                    max_results=max_results
                )
                
                if not messages:
                    return f"No emails found matching query: {query}"
                
                results = []
                for msg in messages[:max_results]:
                    details = gmail_interact.get_email_message_details(self.gmail_service, msg['id'])
                    results.append(f"ID: {msg['id']}, Subject: {details['subject']}, From: {details['sender']}, Date: {details['date']}")
                
                return f"Found {len(results)} emails:\\n" + "\\n".join(results)
            except Exception as e:
                return f"Error searching emails: {str(e)}"
        
        @tool
        def get_email_details(message_id: str) -> str:
            """Get detailed information about a specific email by its ID"""
            try:
                details = gmail_interact.get_email_message_details(self.gmail_service, message_id)
                return f"""Email Details:
Subject: {details['subject']}
From: {details['sender']}
Date: {details['date']}
Body Preview: {details['snippet'][:200]}...
Has Attachments: {details['has_attachments']}"""
            except Exception as e:
                return f"Error getting email details: {str(e)}"
        
        @tool
        def list_labels() -> str:
            """Get all Gmail labels/folders available"""
            try:
                labels = gmail_interact.list_labels(self.gmail_service)
                label_list = [f"{label['name']} (ID: {label['id']})" for label in labels]
                return f"Available labels:\\n" + "\\n".join(label_list)
            except Exception as e:
                return f"Error getting labels: {str(e)}"
        
        @tool
        def trash_email(message_id: str) -> str:
            """Move an email to trash by its ID"""
            try:
                gmail_interact.trash_email(self.gmail_service, 'me', message_id)
                return f"Successfully moved email {message_id} to trash"
            except Exception as e:
                return f"Error trashing email: {str(e)}"
        
        @tool
        def count_emails_today() -> str:
            """Count emails received today"""
            try:
                count = gmail_interact.count_emails_today(self.gmail_service)
                return f"You received {count} emails today"
            except Exception as e:
                return f"Error counting today's emails: {str(e)}"
        
        @tool
        def count_emails_this_week() -> str:
            """Count emails received this week"""
            try:
                count = gmail_interact.count_emails_this_week(self.gmail_service)
                return f"You received {count} emails this week"
            except Exception as e:
                return f"Error counting this week's emails: {str(e)}"
        
        @tool
        def count_emails_this_month() -> str:
            """Count emails received this month"""
            try:
                count = gmail_interact.count_emails_this_month(self.gmail_service)
                return f"You received {count} emails this month"
            except Exception as e:
                return f"Error counting this month's emails: {str(e)}"
        
        @tool
        def get_email_stats() -> str:
            """Get comprehensive email statistics"""
            try:
                stats = gmail_interact.get_email_stats_summary(self.gmail_service)
                return f"""Email Statistics:
Total emails: {stats.get('total_emails', 'Unknown')}
Unread emails: {stats.get('unread_emails', 'Unknown')}
Emails today: {stats.get('emails_today', 'Unknown')}
Emails this week: {stats.get('emails_this_week', 'Unknown')}
Emails this month: {stats.get('emails_this_month', 'Unknown')}"""
            except Exception as e:
                return f"Error getting email stats: {str(e)}"
        
        return [
            search_emails,
            get_email_details,
            list_labels,
            trash_email,
            count_emails_today,
            count_emails_this_week,
            count_emails_this_month,
            get_email_stats
        ]
    
    def chat(self, message: str, chat_history=None) -> str:
        """Process a user message and return AI response"""
        try:
            if chat_history is None:
                chat_history = []
            
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": chat_history
            })
            
            return response["output"]
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def get_available_tools(self) -> list:
        """Return list of available tool names"""
        return [tool.name for tool in self.tools]
