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
        {/* Avatar + bubble */}
        <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <div
            className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm shadow ${
              isUser
                ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-blue-500/20'
                : isDarkMode
                ? 'bg-white/10 text-gray-200 shadow-black/20'
                : 'bg-slate-200 text-slate-700 shadow-slate-300/50'
            }`}
          >
            {isUser ? '👤' : '🏋️‍♀️'}
          </div>

          {/* Bubble */}
          <div
            className={`px-4 py-3 rounded-2xl max-w-full ring-1 ring-inset theme-transition ${
              isUser
                ? (isDarkMode
                    ? 'bg-gradient-to-br from-brand-500 to-accent-500 text-white ring-white/10 shadow-lg shadow-brand-600/25 rounded-br-md'
                    : 'bg-gradient-to-br from-brand-600 to-accent-600 text-white ring-white/10 shadow-lg shadow-brand-600/25 rounded-br-md')
                : isDarkMode
                ? 'bg-[#0f1a33] text-gray-100 ring-white/10 shadow-sm rounded-bl-md'
                : 'bg-white text-gray-900 ring-slate-200 shadow-sm rounded-bl-md'
            }`}
          >
            <div className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
            </div>

            {/* Timestamp */}
            <div
              className={`text-[11px] mt-1 ${
                isUser ? 'text-blue-100/90' : isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}
            >
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>

        {/* Error indicator */}
        {message.error && (
          <div className={`mt-1 text-xs px-2 ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
            {message.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
