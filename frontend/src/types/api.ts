// API types matching the backend
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface AgentQueryResponse {
  question: string;
  answer: string;
  conversation_id: string;
  verbose: boolean;
  reasoning_trace?: string[];
}

export interface AgentQueryRequest {
  question: string;
  verbose?: boolean;
  conversation_id?: string;
}

// Chat-specific types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  conversationId: string | null;
  error: string | null;
}