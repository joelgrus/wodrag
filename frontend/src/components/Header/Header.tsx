import React from 'react';
import { ReactComponent as WodragLogo } from '../../assets/logo-wodrag.svg';

interface HeaderProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  onNewChat: () => void;
}

const Header: React.FC<HeaderProps> = ({ isDarkMode, onToggleTheme, onNewChat }) => {
  const handleNewChat = () => {
    onNewChat();
  };

  return (
    <header
      className={`sticky top-0 z-20 backdrop-blur theme-transition border-b px-4 sm:px-6 py-3 ${
        isDarkMode ? 'bg-[#0c1222]/80 border-white/10' : 'bg-white/70 border-slate-200'
      }`}
      style={{ WebkitBackdropFilter: 'blur(6px)', backdropFilter: 'blur(6px)' }}
    >
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9">
              <WodragLogo />
            </div>
            <div>
              <div className="text-sm uppercase tracking-wider font-semibold text-brand-600">Wodrag</div>
              <h1 className="leading-tight font-semibold text-base sm:text-lg">
                CrossFit AI Coach
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={handleNewChat}
              className={`inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg font-medium theme-transition ring-1 ring-inset shadow-sm ${
                isDarkMode
                  ? 'bg-brand-600 hover:bg-brand-700 text-white ring-white/10'
                  : 'bg-brand-600 hover:bg-brand-700 text-white ring-brand-600/20'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                <path d="M12 5v14m-7-7h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              New Chat
            </button>

            <button
              onClick={onToggleTheme}
              className={`inline-flex items-center justify-center w-10 h-10 rounded-lg theme-transition ring-1 ring-inset ${
                isDarkMode
                  ? 'hover:bg-white/10 text-gray-200 ring-white/10'
                  : 'hover:bg-slate-100 text-slate-700 ring-slate-200'
              }`}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {isDarkMode ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v2m0 14v2m9-9h-2M5 12H3m15.364-6.364l-1.414 1.414M7.05 16.95l-1.414 1.414m12.728 0l-1.414-1.414M7.05 7.05L5.636 5.636M12 8a4 4 0 100 8 4 4 0 000-8z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
