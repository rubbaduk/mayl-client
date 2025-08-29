import { useState } from 'react'
import './App.css'
import Login from './components/login'
import MailPage from './components/main/MailPage'


function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  if (!isAuthenticated) {
    return <Login onAuthSuccess={handleAuthSuccess} />;
  }

  // after login
  return <MailPage/>
}

export default App;
