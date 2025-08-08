import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import LoadingIndicator from './LoadingIndicator';
import { ChatMessage, ChatState } from '../../types/api';
import { apiService } from '../../services/api';

interface ChatInterfaceProps {
  isDarkMode: boolean;
  resetTrigger?: number; // Increment to trigger reset
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isDarkMode, resetTrigger }) => {
  const getInitialState = (): ChatState => ({
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

  const [chatState, setChatState] = useState<ChatState>(getInitialState);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<{ focus: () => void } | null>(null);

  // Reset chat when resetTrigger changes
  useEffect(() => {
    if (resetTrigger && resetTrigger > 0) {
      setChatState(getInitialState());
    }
  }, [resetTrigger]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatState.messages]);

  // Focus input after loading completes
  useEffect(() => {
    if (!chatState.isLoading) {
      inputRef.current?.focus();
    }
  }, [chatState.isLoading]);

  const handleSendMessage = async (message: string) => {
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
      error: null,
    }));

    try {
      // Make API call to backend
      const request: any = {
        question: message,
        verbose: false,
      };
      
      // Only include conversation_id if we have one
      if (chatState.conversationId) {
        request.conversation_id = chatState.conversationId;
      }
      
      const response = await apiService.queryAgent(request);

      if (response.success && response.data) {
        const data = response.data; // TypeScript now knows data is not null
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.answer,
          timestamp: new Date(),
        };

        setChatState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          isLoading: false,
          conversationId: data.conversation_id,
          error: null,
        }));
      } else {
        // API call succeeded but returned an error
        setChatState(prev => ({
          ...prev,
          isLoading: false,
          error: response.error || 'Failed to get response from AI',
        }));
      }
    } catch (error) {
      // Network or other errors
      console.error('Error sending message:', error);
      setChatState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Network error. Please check your connection and try again.',
      }));
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages Container */}
      <div
        ref={scrollContainerRef}
        className={`flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 theme-transition ${
          isDarkMode ? 'bg-transparent' : 'bg-transparent'
        }`}
      >
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
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message Input */}
      <MessageInput
        ref={inputRef}
        onSendMessage={handleSendMessage}
        disabled={chatState.isLoading}
        isDarkMode={isDarkMode}
      />
    </div>
  );
};

export default ChatInterface;
