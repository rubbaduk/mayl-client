import { useState, useEffect } from 'react'
import './App.css'
declare global {
  interface Window {
    google: any;
  }
}
function App() {

  function handleCallbackResponse(response: any){
    console.log("Encoded JWT ID token: " + response.credential);
  }
  useEffect(() => {
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        callback: handleCallbackResponse
      });

      window.google.accounts.id.renderButton(
        document.getElementById("signIn"),
        {theme: "outline", size: "large"}
      );
    }
  }, []);
  return (
    <>
      <div id="signIn"></div>
    </>
  )
}

export default App
