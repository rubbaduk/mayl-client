import React, { useState } from 'react';
import { 
  InboxIcon, 
  StarIcon, 
  ClockIcon, 
  PaperAirplaneIcon, 
  DocumentTextIcon, 
  TrashIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon
} from '@heroicons/react/24/outline';

interface SidebarItem {
  name: string;
  icon: React.ReactNode;
  count?: number;
}

interface SidebarProps {
    collapsed: boolean;
    onToggleCollapse: () => void;
}

const Sidebar = ({collapsed, onToggleCollapse}: SidebarProps) => {

  const sidebarItems: SidebarItem[] = [
    { name: 'Inbox', icon: <InboxIcon className="w-5 h-5" />, count: 120 },
    { name: 'Starred', icon: <StarIcon className="w-5 h-5" /> },
    { name: 'Snoozed', icon: <ClockIcon className="w-5 h-5" /> },
    { name: 'Sent', icon: <PaperAirplaneIcon className="w-5 h-5" /> },
    { name: 'Drafts', icon: <DocumentTextIcon className="w-5 h-5" />, count: 12 },
    { name: 'Trash', icon: <TrashIcon className="w-5 h-5" /> },
  ];

  return (
    <aside className={`h-screen transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      <nav className="h-full flex flex-col bg-white border-r border-gray-200 shadow-sm">
        <div className="p-4 pb-2 flex justify-between items-center">
          <div className={`overflow-hidden transition-all ${collapsed ? 'w-0' : 'w-32'}`}>
            <img 
              src="https://www.google.com/gmail/about/static/images/logo-gmail.png" 
              alt="Gmail"
              className="h-8"
            />
          </div>
          <button 
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg bg-gray-50 hover:bg-gray-100"
          >
            {collapsed ? 
              <ChevronDoubleRightIcon className="w-5 h-5 text-gray-600" /> : 
              <ChevronDoubleLeftIcon className="w-5 h-5 text-gray-600" />
            }
          </button>
        </div>

        <div className="flex-1 px-3 py-4 space-y-1">
          {sidebarItems.map((item) => (
            <div 
              key={item.name}
              className={`flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-100 text-gray-700 ${
                item.name === 'Inbox' ? 'bg-blue-50 text-blue-600 font-medium' : ''
              }`}
            >
              <div className="w-6 flex justify-center">
                {item.icon}
              </div>
              {!collapsed && (
                <div className="flex-1 flex justify-between items-center ml-3">
                  <span>{item.name}</span>
                  {item.count && (
                    <span className="text-xs bg-gray-200 rounded-full px-2 py-0.5">
                      {item.count}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;