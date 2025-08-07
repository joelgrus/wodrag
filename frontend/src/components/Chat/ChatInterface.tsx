import React, { useState } from 'react';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import LoadingIndicator from './LoadingIndicator';
import { ChatMessage, ChatState } from '../../types/api';

interface ChatInterfaceProps {
  isDarkMode: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isDarkMode }) => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [
      {
        id: '1',
        role: 'assistant',
        content: 'Hi! I\'m your CrossFit AI Coach. I can help you find workouts, suggest modifications, explain movements, and answer any CrossFit-related questions. What would you like to know?',
        timestamp: new Date(),
      }
    ],
    isLoading: false,
    conversationId: null,
    error: null,
  });

  const handleSendMessage = (message: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
    }));

    // TODO: Implement API call
    // For now, simulate a response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'This is a placeholder response. API integration will be implemented in Phase 2.',
        timestamp: new Date(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));
    }, 1500);
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatState.messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            isDarkMode={isDarkMode}
          />
        ))}
        
        {chatState.isLoading && (
          <LoadingIndicator isDarkMode={isDarkMode} />
        )}
        
        {chatState.error && (
          <div className={`p-4 rounded-lg ${
            isDarkMode 
              ? 'bg-red-900/20 border border-red-800 text-red-200' 
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            <p className="text-sm">Error: {chatState.error}</p>
          </div>
        )}
      </div>
      
      {/* Message Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={chatState.isLoading}
        isDarkMode={isDarkMode}
      />
    </div>
  );
};

export default ChatInterface;