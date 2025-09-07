import { useEffect, useState } from 'react';

interface Email {
  id: string;
  from: string;
  subject: string;
  preview: string;
  time: string;
  read: boolean;
  starred: boolean;
  important: boolean;
  hasAttachment: boolean;
  labels?: string[];
}

const MailList = () => {
    const [, setEmails] = useState<Email[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchEmails = async () => {
    setLoading(true);
    setError(null);
    try {
        const token = localStorage.getItem('sessionToken');
        if (!token) {
            throw new Error('no authentication token found. Please log in again.');
        }
        
        const response = await fetch('http://localhost:8000/api/gmail/messages', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.status === 401) {
            // clear invalid token and redirect to login
            localStorage.removeItem('sessionToken');
            window.location.href = '/';
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to fetch emails');
        }
        
        const data = await response.json();
        setEmails(processEmailData(data.messages));
    } catch (err) {
        console.error('Error fetching emails:', err);
        setError('Failed to load emails. Please try again.');
    } finally {
        setLoading(false);
    }
};

  const processEmailData = (messages: any[]): Email[] => {
    return messages.map(msg => ({
      id: msg.id,
      from: msg.payload.headers.find((h: any) => h.name === 'From')?.value || 'Unknown',
      subject: msg.payload.headers.find((h: any) => h.name === 'Subject')?.value || '(No subject)',
      preview: msg.snippet,
      time: formatDate(msg.internalDate),
      read: !msg.labelIds?.includes('UNREAD'),
      starred: msg.labelIds?.includes('STARRED') || false,
      important: msg.labelIds?.includes('IMPORTANT') || false,
      hasAttachment: hasAttachment(msg),
      labels: msg.labelIds?.filter((label: string) => 
        !['INBOX', 'SENT', 'DRAFT', 'IMPORTANT', 'STARRED', 'UNREAD'].includes(label)
      )
    }));
  };

  const hasAttachment = (message: any): boolean => {
    return message.payload.parts?.some((part: any) => part.filename && part.filename.length > 0) || false;
  };

  const formatDate = (timestamp: string): string => {
    const date = new Date(parseInt(timestamp));
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-red-500 mb-4">{error}</p>
        <button 
          onClick={fetchEmails}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

};


export default MailList;
