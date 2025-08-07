# WoDrag Web App Development Plan

This document outlines the development plan for the WoDrag web application - a clean, minimal chat interface for our CrossFit AI coach.

## 🎯 Overview

**Goal**: Build a simple, responsive chat interface that connects to our existing conversation API.

**Tech Stack**: React + TypeScript + Vite + Tailwind CSS

**Architecture**: Frontend container + existing backend container + database container

## 📋 Development Phases

### Phase 1: Project Setup & Basic UI ⏳
**Goal**: Get React app running with static chat interface

**Tasks**:
- [ ] Initialize Vite + React + TypeScript project in `/frontend`
- [ ] Setup Tailwind CSS
- [ ] Create basic project structure (components, hooks, services)
- [ ] Build static chat interface layout
- [ ] Implement responsive design (mobile-first)
- [ ] Add dark/light theme toggle (localStorage persistence)
- [ ] Create basic components:
  - [ ] `App.tsx` - Main application
  - [ ] `ChatInterface.tsx` - Main chat container
  - [ ] `MessageBubble.tsx` - Individual message display
  - [ ] `MessageInput.tsx` - Input field + send button
  - [ ] `Header.tsx` - App header with title
  - [ ] `NewChatButton.tsx` - New conversation button
  - [ ] `LoadingIndicator.tsx` - "AI is thinking..." state

### Phase 2: API Integration ⏳
**Goal**: Connect to existing backend API

**Tasks**:
- [ ] Create TypeScript types matching backend API
- [ ] Implement `ChatApiService` class
- [ ] Create `useChat` hook for state management
- [ ] Connect message input to API calls
- [ ] Handle API responses and update UI
- [ ] Implement error handling (inline in chat)
- [ ] Add loading states during API calls
- [ ] Test with actual backend API

### Phase 3: Conversation Management ⏳
**Goal**: Handle conversation state and new chat functionality

**Tasks**:
- [ ] Implement conversation ID management
- [ ] Add "New Conversation" functionality
- [ ] Add confirmation dialog for new conversation
- [ ] Implement message history display
- [ ] Add auto-scroll to latest message
- [ ] Handle conversation context properly
- [ ] Add welcome message for new conversations

### Phase 4: Polish & UX Improvements ⏳
**Goal**: Improve user experience and add final touches

**Tasks**:
- [ ] Improve error messages and error handling
- [ ] Add message timestamps (subtle)
- [ ] Implement proper loading animations
- [ ] Add keyboard shortcuts (Enter to send, Ctrl+N for new chat)
- [ ] Optimize mobile experience
- [ ] Add proper focus management
- [ ] Implement proper dark/light theme styles
- [ ] Add favicon and meta tags

### Phase 5: Containerization & Deployment ⏳
**Goal**: Package frontend for production deployment

**Tasks**:
- [ ] Create production build process
- [ ] Create Docker container for frontend (Nginx)
- [ ] Update docker-compose.yml to include frontend
- [ ] Configure reverse proxy routing
- [ ] Test full-stack deployment
- [ ] Document deployment process

## 📁 Project Structure

```
wodrag/
├── frontend/                   # New React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── LoadingIndicator.tsx
│   │   │   ├── Header/
│   │   │   │   ├── Header.tsx
│   │   │   │   └── NewChatButton.tsx
│   │   │   └── common/
│   │   │       └── ErrorBoundary.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   ├── useTheme.ts
│   │   │   └── useApi.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── api.ts
│   │   ├── styles/
│   │   │   └── index.css
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml         # Updated to include frontend
└── (existing backend files)
```

## 🎨 UI/UX Design Specifications

### Layout (Desktop)
```
┌─────────────────────────────────────────────┐
│ 🏋️ WoDrag - CrossFit AI Coach    🌓 [New] │ ← Header (h-16)
├─────────────────────────────────────────────┤
│                                             │
│  👤 What is the Murph workout?              │ ← User message
│                                             │
│  🤖 Murph is a hero workout consisting      │ ← Assistant message  
│     of a 1-mile run, 100 pull-ups...       │
│                                             │
│  👤 Make it easier for a beginner          │
│                                             │
│  🤖 Here's a scaled version of Murph...    │
│                                             │
│  💭 AI is thinking...                      │ ← Loading state
│                                             │
├─────────────────────────────────────────────┤
│ [Type your message here...]           [→]  │ ← Input (h-16)
└─────────────────────────────────────────────┘
```

### Mobile Layout
- Stack layout, full width
- Larger touch targets
- Collapsible header on scroll
- Fixed input at bottom

### Color Scheme
**Light Theme**:
- Background: `bg-gray-50`
- User messages: `bg-blue-500 text-white`
- Assistant messages: `bg-white border`
- Input: `bg-white border`

**Dark Theme**:
- Background: `bg-gray-900`
- User messages: `bg-blue-600 text-white`
- Assistant messages: `bg-gray-800 text-gray-100`
- Input: `bg-gray-800 text-gray-100`

## 🔌 API Integration Details

### TypeScript Types
```typescript
// Match existing backend API
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

interface AgentQueryResponse {
  question: string;
  answer: string;
  conversation_id: string;
  verbose: boolean;
  reasoning_trace?: string[];
}

interface AgentQueryRequest {
  question: string;
  verbose?: boolean;
  conversation_id?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}
```

### API Service Implementation
```typescript
class ChatApiService {
  private baseUrl = '/api/v1'; // Relative path to backend
  
  async sendMessage(
    question: string, 
    conversationId?: string,
    verbose = false
  ): Promise<ApiResponse<AgentQueryResponse>> {
    // POST /api/v1/agent/query
    // Handle errors, timeouts, retries
  }
  
  async healthCheck(): Promise<boolean> {
    // GET /api/v1/health
  }
}
```

### State Management Pattern
```typescript
const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (content: string) => {
    // Add user message immediately
    // Call API
    // Add assistant response
    // Handle errors
  };

  const startNewConversation = () => {
    // Clear messages and conversation ID
  };

  return { messages, isLoading, sendMessage, startNewConversation, error };
};
```

## 🐳 Docker Configuration

### Frontend Dockerfile
```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Updated docker-compose.yml
```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    
  backend:
    # existing backend config
    
  postgres:
    # existing database config
```

## 📱 Responsive Design Strategy

### Breakpoints (Tailwind)
- **Mobile**: `default` (< 640px)
- **Tablet**: `sm:` (≥ 640px)
- **Desktop**: `lg:` (≥ 1024px)

### Mobile Optimizations
- Touch-friendly button sizes (min 44px)
- Proper viewport meta tag
- Swipe gestures for new conversation
- Auto-resize textarea for message input
- Fixed positioning for input to avoid keyboard issues

## ✅ Definition of Done

Each phase is complete when:
- [ ] All tasks in phase are implemented
- [ ] Code follows TypeScript best practices
- [ ] Responsive design works on mobile and desktop
- [ ] Dark/light theme toggle works properly
- [ ] Error handling is implemented
- [ ] Basic accessibility standards are met
- [ ] Manual testing passes on Chrome and Safari
- [ ] Code is committed with clear commit messages

## 🚀 Future Enhancements (Post-MVP)

- Message persistence across browser sessions
- Conversation history/list view
- Export conversation feature
- Voice input/output
- Workout visualization components
- Improved welcome flow/onboarding
- Performance optimizations (message virtualization)
- PWA capabilities (offline support)

## 📝 Development Notes

### Getting Started
1. Create new branch: `git checkout -b webapp`
2. Initialize React project in `/frontend`
3. Start backend API server for development
4. Begin with Phase 1 tasks

### API Development
- Backend API already exists at `/api/v1/agent/query`
- Use relative paths: frontend proxy will handle routing
- Test API integration early and often

### Deployment Strategy
- Development: `npm run dev` + separate backend server
- Production: Docker containers with Nginx reverse proxy
- Single VPS deployment with docker-compose

---

This plan provides a clear roadmap from basic React setup to production deployment, with each phase building incrementally on the previous one.