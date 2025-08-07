import React, { useState } from 'react';
import Header from './components/Header/Header';
import ChatInterface from './components/Chat/ChatInterface';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Initialize theme from localStorage or system preference
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const [resetTrigger, setResetTrigger] = useState(0);

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  const handleNewChat = () => {
    setResetTrigger(prev => prev + 1);
  };

  return (
    <div className={`min-h-screen transition-colors duration-200 ${
      isDarkMode 
        ? 'bg-gray-900 text-gray-100' 
        : 'bg-gray-50 text-gray-900'
    }`}>
      <div className="flex flex-col h-screen max-w-4xl mx-auto">
        <Header 
          isDarkMode={isDarkMode} 
          onToggleTheme={toggleTheme}
          onNewChat={handleNewChat}
        />
        <ChatInterface 
          isDarkMode={isDarkMode} 
          resetTrigger={resetTrigger}
        />
      </div>
    </div>
  );
}

export default App;
