import React, { useEffect, useState } from 'react';
import Header from './components/Header/Header';
import ChatInterface from './components/Chat/ChatInterface';
import WorkoutPage from './pages/WorkoutPage';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Initialize theme from localStorage or system preference
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const [resetTrigger, setResetTrigger] = useState(0);
  // Prefer hash-based routing for dev server compatibility
  const getPath = () => (window.location.hash ? window.location.hash.slice(1) : window.location.pathname);
  const [path, setPath] = useState<string>(getPath());

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  const handleNewChat = () => {
    // Navigate to root and reset chat
    if (window.location.pathname !== '/') {
      window.history.pushState({}, '', '/');
      setPath('/');
    }
    setResetTrigger(prev => prev + 1);
  };

  // Lightweight router: update on back/forward or hash changes
  useEffect(() => {
    const onChange = () => setPath(getPath());
    window.addEventListener('popstate', onChange);
    window.addEventListener('hashchange', onChange);
    // If user loads a deep link like /workouts/... in dev, redirect to hash route
    if (!window.location.hash && /^\/workouts\//.test(window.location.pathname)) {
      const newHash = `#${window.location.pathname}${window.location.search}`;
      window.location.replace(newHash);
    }
    return () => {
      window.removeEventListener('popstate', onChange);
      window.removeEventListener('hashchange', onChange);
    };
  }, []);

  // Sync a global theme class to <html> for background fallbacks
  useEffect(() => {
    const root = document.documentElement;
    if (isDarkMode) {
      root.classList.add('theme-dark');
      root.classList.remove('theme-light');
    } else {
      root.classList.add('theme-light');
      root.classList.remove('theme-dark');
    }
  }, [isDarkMode]);

  return (
    <div
      className={`min-h-screen theme-transition ${
        isDarkMode
          ? 'text-gray-100 app-gradient-dark bg-dotgrid-dark'
          : 'text-gray-900 app-gradient-light bg-dotgrid-light'
      }`}
      style={{ minHeight: '100vh' }}
    >
      <div className="flex flex-col" style={{ minHeight: '100vh' }}>
        <Header
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
          onNewChat={handleNewChat}
        />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div
            className={`mx-auto max-w-4xl rounded-2xl border backdrop-blur theme-transition shadow-elevated ${
              isDarkMode
                ? 'bg-white/10 border-white/10'
                : 'bg-white/90 border-slate-200'
            }`}
            style={{
              /* Subtle glass effect for light theme */
              WebkitBackdropFilter: 'blur(8px)',
              backdropFilter: 'blur(8px)'
            }}
          >
            {/^\/workouts\//.test(path) ? (
              <WorkoutPage isDarkMode={isDarkMode} />
            ) : (
              <ChatInterface isDarkMode={isDarkMode} resetTrigger={resetTrigger} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
