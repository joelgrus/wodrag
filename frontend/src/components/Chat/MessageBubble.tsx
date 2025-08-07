import React from 'react';
import { ChatMessage } from '../../types/api';

interface MessageBubbleProps {
  message: ChatMessage;
  isDarkMode: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isDarkMode }) => {
  const isUser = message.role === 'user';
  
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Avatar */}
        <div className={`flex items-end space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${
            isUser 
              ? (isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white')
              : (isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-600')
          }`}>
            {isUser ? '👤' : '🏋️‍♀️'}
          </div>
          
          {/* Message Content */}
          <div className={`px-4 py-3 rounded-2xl max-w-full ${
            isUser
              ? (isDarkMode 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-blue-600 text-white')
              : (isDarkMode
                  ? 'bg-gray-700 text-gray-100'
                  : 'bg-gray-100 text-gray-900')
          } ${
            isUser 
              ? 'rounded-br-md' 
              : 'rounded-bl-md'
          }`}>
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
            
            {/* Timestamp */}
            <div className={`text-xs mt-1 ${
              isUser 
                ? 'text-blue-100' 
                : (isDarkMode ? 'text-gray-400' : 'text-gray-500')
            }`}>
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>
        
        {/* Error indicator */}
        {message.error && (
          <div className={`mt-1 text-xs px-2 ${
            isDarkMode ? 'text-red-400' : 'text-red-600'
          }`}>
            {message.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;