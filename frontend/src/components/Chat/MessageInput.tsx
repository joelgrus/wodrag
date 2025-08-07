import React, { useState, KeyboardEvent } from 'react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  isDarkMode: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({ 
  onSendMessage, 
  disabled = false, 
  isDarkMode 
}) => {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSendMessage(trimmed);
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={`border-t p-4 ${
      isDarkMode 
        ? 'border-gray-700 bg-gray-800' 
        : 'border-gray-200 bg-white'
    }`}>
      <div className="flex items-end space-x-3">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about CrossFit workouts, movements, or training..."
            disabled={disabled}
            className={`w-full px-4 py-3 rounded-lg border resize-none transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              isDarkMode
                ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400'
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            rows={1}
            style={{
              minHeight: '48px',
              maxHeight: '120px',
            }}
          />
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={disabled || !message.trim()}
          className={`px-4 py-3 rounded-lg font-medium transition-all flex-shrink-0 ${
            disabled || !message.trim()
              ? (isDarkMode 
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed')
              : (isDarkMode
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-blue-500/25'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-blue-500/25')
          }`}
          aria-label="Send message"
        >
          <svg 
            className="w-5 h-5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
            />
          </svg>
        </button>
      </div>
      
      <div className={`text-xs mt-2 ${
        isDarkMode ? 'text-gray-400' : 'text-gray-500'
      }`}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
};

export default MessageInput;