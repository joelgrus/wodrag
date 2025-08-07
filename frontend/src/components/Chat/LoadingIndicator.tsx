import React from 'react';

interface LoadingIndicatorProps {
  isDarkMode: boolean;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ isDarkMode }) => {
  return (
    <div className="flex justify-start">
      <div className="flex items-end space-x-2">
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${
          isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-600'
        }`}>
          🏋️‍♀️
        </div>
        
        {/* Loading bubble */}
        <div className={`px-4 py-3 rounded-2xl rounded-bl-md ${
          isDarkMode
            ? 'bg-gray-700'
            : 'bg-gray-100'
        }`}>
          <div className="flex space-x-1">
            <div 
              className={`w-2 h-2 rounded-full animate-bounce ${
                isDarkMode ? 'bg-gray-400' : 'bg-gray-500'
              }`}
              style={{ animationDelay: '0ms' }}
            ></div>
            <div 
              className={`w-2 h-2 rounded-full animate-bounce ${
                isDarkMode ? 'bg-gray-400' : 'bg-gray-500'
              }`}
              style={{ animationDelay: '150ms' }}
            ></div>
            <div 
              className={`w-2 h-2 rounded-full animate-bounce ${
                isDarkMode ? 'bg-gray-400' : 'bg-gray-500'
              }`}
              style={{ animationDelay: '300ms' }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;