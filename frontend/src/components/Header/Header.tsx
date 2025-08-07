import React from 'react';

interface HeaderProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

const Header: React.FC<HeaderProps> = ({ isDarkMode, onToggleTheme }) => {
  const handleNewChat = () => {
    // TODO: Implement new chat functionality
    console.log('New chat clicked');
  };

  return (
    <header className={`border-b px-6 py-4 ${
      isDarkMode 
        ? 'border-gray-700 bg-gray-800' 
        : 'border-gray-200 bg-white'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl font-bold text-blue-600">🏋️‍♀️</div>
          <h1 className="text-xl font-semibold">CrossFit AI Coach</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={handleNewChat}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isDarkMode
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            New Chat
          </button>
          
          <button
            onClick={onToggleTheme}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'hover:bg-gray-700 text-gray-300'
                : 'hover:bg-gray-100 text-gray-600'
            }`}
            aria-label="Toggle theme"
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;