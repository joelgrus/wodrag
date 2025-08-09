import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import LoadingIndicator from './LoadingIndicator';
import Credits from '../Credits/Credits';
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
        content: `Hi! I'm your CrossFit Research Assistant. I can help you explore and analyze our database of 8,861+ CrossFit.com Workout of the Day (WOD) entries from 2001-2025.

Here are some things you can ask me:

**Workout Information**: "What is the workout Murph?"
**Historical Data**: "When was the last time Murph was programmed?"
**Data Analysis**: "How many workouts with pull-ups in 2023?"
**Discovery**: "What was the first workout that involved swimming?"
**Search & Filter**: "Find me workouts that include both pull-ups and push-ups"
**Custom Workouts**: "Create for me a workout that has a lot of sit-ups in it!"

What would you like to research?`,
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
      // Focus the input after resetting
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [resetTrigger]);

  // Focus input on initial mount
  useEffect(() => {
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

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
            chatState.error.toLowerCase().includes('rate limit') || chatState.error.toLowerCase().includes('too many requests')
              ? isDarkMode 
                ? 'bg-yellow-900/20 border border-yellow-700 text-yellow-200' 
                : 'bg-yellow-50 border border-yellow-300 text-yellow-800'
              : isDarkMode 
                ? 'bg-red-900/20 border border-red-800 text-red-200' 
                : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            {chatState.error.toLowerCase().includes('rate limit') || chatState.error.toLowerCase().includes('too many requests') ? (
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 mt-0.5">
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Rate limit reached</p>
                  <p className="text-sm mt-1">{chatState.error.replace(/^Error: /, '')}</p>
                </div>
              </div>
            ) : (
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 mt-0.5">
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Something went wrong</p>
                  <p className="text-sm mt-1">{chatState.error.replace(/^Error: /, '')}</p>
                </div>
              </div>
            )}
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
      
      {/* Credits */}
      <Credits 
        isDarkMode={isDarkMode} 
        className={`py-4 px-6 border-t theme-transition ${
          isDarkMode ? 'border-white/10' : 'border-slate-200'
        }`} 
      />
    </div>
  );
};

export default ChatInterface;
