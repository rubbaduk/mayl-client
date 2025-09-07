import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

const MailPage = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className="flex flex-col h-screen w-full">
      <Header onMenuClick={toggleSidebar} />
      <div className="flex flex-1 w-full overflow-hidden">
        <Sidebar collapsed={sidebarCollapsed} />
        
        
        <main className="flex-1 w-full overflow-auto bg-gray-50">
          {/* mail content */}
        </main>
      </div>
    </div>
  );
};

export default MailPage;