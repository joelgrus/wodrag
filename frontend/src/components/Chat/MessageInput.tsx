import React, { useState, KeyboardEvent, forwardRef, useImperativeHandle, useRef } from 'react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  isDarkMode: boolean;
}

const MessageInput = forwardRef<{ focus: () => void }, MessageInputProps>(({ 
  onSendMessage, 
  disabled = false, 
  isDarkMode 
}, ref) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus();
    }
  }));

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
    <div
      className={`border-t p-4 sticky bottom-0 z-10 backdrop-blur theme-transition ${
        isDarkMode ? 'border-white/10 bg-[#0c1222]/80' : 'border-slate-200 bg-white/70'
      }`}
      style={{ WebkitBackdropFilter: 'blur(6px)', backdropFilter: 'blur(6px)' }}
    >
      <div className="flex items-end gap-3">
        <div className={`flex-1 flex items-center gap-2 rounded-xl ring-1 ring-inset px-3 py-1.5 theme-transition ${
          isDarkMode ? 'bg-white/10 ring-white/10' : 'bg-white ring-slate-200'
        }`}>
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about CrossFit workouts, movements, or training..."
            disabled={disabled}
            className={`w-full px-2 py-2 rounded-md resize-none focus:outline-none text-sm theme-transition ${
              isDarkMode
                ? 'bg-transparent text-gray-100 placeholder-gray-400'
                : 'bg-transparent text-gray-900 placeholder-gray-500'
            } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
            rows={1}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />

          <button
            onClick={handleSubmit}
            disabled={disabled || !message.trim()}
            className={`inline-flex items-center justify-center w-10 h-10 rounded-lg font-medium transition-all ${
              disabled || !message.trim()
                ? isDarkMode
                  ? 'bg-white/5 text-gray-500 cursor-not-allowed'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-br from-brand-600 to-accent-600 text-white shadow-md hover:shadow-brand-600/30 hover:translate-y-[-1px]'
            }`}
            aria-label="Send message"
            title="Send"
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
      </div>

      <div className={`text-[11px] mt-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
});

MessageInput.displayName = 'MessageInput';

export default MessageInput;
