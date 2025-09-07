import React, { useEffect, useRef, useState } from 'react'

interface UserProfile {
  name: string;
  email: string;
  picture?: string;
}

interface HeaderProps {
  userProfile?: UserProfile;
  onMenuClick: () => void;
}



const Header: React.FC<HeaderProps>= ({userProfile, onMenuClick}) => {

  const [showDropdown, setShowDropdown] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // close on outside click

  useEffect(() => {
    function outsideClick(e: MouseEvent){
      if (menuRef.current && !menuRef.current.contains(e.target as Node)){
        setShowDropdown(false);
      }
    }
    if (showDropdown){
      document.addEventListener('click', outsideClick);
    }
    return () => {
      document.removeEventListener('click', outsideClick);
    };
  }, [showDropdown]);

  // use initials if no pp
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const handleProfileClick = () => {
    setShowDropdown(!showDropdown);
  };

  useEffect(() => {

  })

  
  
  return (
    <header className="flex items-center justify-between px-4 py-2 bg-gmail-lightgray border-b border-gray-200 w-full gap-2">
      {/* left side */}
      <div className="flex items-center gap-2">
        <button onClick = {onMenuClick} className="p-2 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gmail-blue">
          <svg className="w-6 h-6 text-gmail-gray" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className='ml-3 font-sans text-2xl italic font-extralight text-gmail-gray'>mayl</h1>
      </div>

      {/* search bar */}
      <div className="w-150">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg className="w-5 h-5 text-gmail-gray" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search mail or talk to mayl"
            className="w-full py-2.5 pl-10 pr-4 bg-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gmail-blue focus:bg-white transition-all duration-300"
          />
        </div>
      </div>

      {/* profile, settings etc */}
      <div className="relative flex" ref = {menuRef}>
        {/* settings */}
          <button className="p-2 mr-3 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gmail-blue">
            <svg className="w-6 h-6 text-gmail-gray dark:text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
          

          {/* pfp */}
          <button 
            onClick={handleProfileClick}
            className="flex items-center space-x-2 p-1 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gmail-blue"
          >
            {userProfile?.picture ? (
              <img 
                src={userProfile.picture} 
                alt={userProfile.name}
                className="w-8 h-8 rounded-full"
              />
            ) : (
              <div className="w-8 h-8 bg-gmail-blue rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-black">
                  {userProfile ? getInitials(userProfile.name) : 'DD'}
                </span>
              </div>
            )}
          </button>

          {/* user dropdown */}
          {showDropdown && (
            <div className="absolute right-0 mt-12 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  {userProfile?.picture ? (
                    <img 
                      src={userProfile.picture} 
                      alt={userProfile.name}
                      className="w-10 h-10 rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 bg-gmail-blue rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">
                        {userProfile ? getInitials(userProfile.name) : 'U'}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-gray-900">{userProfile?.name || 'User'}</p>
                    <p className="text-sm text-gray-500">{userProfile?.email || 'user@example.com'}</p>
                  </div>
                </div>
              </div>
              <div className="py-2">
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                  Account Settings
                </button>
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                  Privacy & Terms
                </button>
                <hr className="my-2" />
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
    </header>
  );
}

export default Header;