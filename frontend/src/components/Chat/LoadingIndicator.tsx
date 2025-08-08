import React from 'react';

interface LoadingIndicatorProps {
  isDarkMode: boolean;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ isDarkMode }) => {
  return (
    <div className="flex justify-start">
      <div className="flex items-end gap-2">
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm shadow ${
            isDarkMode ? 'bg-white/10 text-gray-200 shadow-black/20' : 'bg-slate-200 text-slate-700 shadow-slate-300/50'
          }`}
        >
          🏋️‍♀️
        </div>

        {/* Loading bubble */}
        <div className={`px-4 py-3 rounded-2xl rounded-bl-md ring-1 ring-inset ${isDarkMode ? 'bg-white/10 ring-white/10' : 'bg-white ring-slate-200 shadow-sm'}`}>
          <div className="flex gap-1 items-center">
            <span className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-400' : 'bg-gray-500'}`} style={{ animationDelay: '0ms' }} />
            <span className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-400' : 'bg-gray-500'}`} style={{ animationDelay: '150ms' }} />
            <span className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-400' : 'bg-gray-500'}`} style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;
