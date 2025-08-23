import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async () => {
    setIsLoading(true);
    try {
      // oauth url from fastapi backend
      const response = await fetch('http://localhost:8000/api/auth/oauth-url');
      const data = await response.json();
      
      // full page redirect
      window.location.href = data.authorization_url;
    } catch (error) {
      console.error('Error getting OAuth URL:', error);
      setIsLoading(false);
    }
  };

  // checking for auth token
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
      localStorage.setItem('sessionToken', token);
      console.log('Authentication successful');
    }
  }, []);


  // MOVE ALL TO LOGIN.TSX LATER
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh' 
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1>Mayl</h1>
        <p>Manage your emails with AI-powered assistance</p>
        
        <button 
          onClick={handleSignIn}
          disabled={isLoading}
          style={{
            backgroundColor: '#4285f4',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '4px',
            fontSize: '16px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.7 : 1
          }}
        >
          {isLoading ? 'Redirecting...' : 'Sign in with Google'}
        </button>
      </div>
    </div>
  );
}

export default App;
