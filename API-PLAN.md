# API Implementation Plan

This document outlines the complete plan for implementing a REST API for the wodrag CrossFit workout search system.

## Overview

The API will expose the existing search and CRUD functionality through HTTP endpoints, enabling web applications and other clients to interact with the 8,861+ workout database.

## Technology Stack

- **Framework**: FastAPI (modern, async, automatic OpenAPI docs)
- **Database**: Existing ParadeDB/PostgreSQL setup 
- **Authentication**: API key-based (simple and secure)
- **Serialization**: Pydantic models (FastAPI native)
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## API Endpoints Design

### Core Search Endpoints (Priority)
- `GET /api/v1/search` - Hybrid search (BM25 + semantic)
- `GET /api/v1/search/semantic` - Semantic similarity search only
- `GET /api/v1/search/text` - BM25 text search only
- `GET /api/v1/query` - Natural language to SQL via DuckDB

### Utility Endpoints
- `GET /api/v1/health` - Health check

### Maybe Later (Auth Required)

#### CRUD Endpoints  
- `GET /api/v1/workouts` - List workouts with pagination/filtering
- `GET /api/v1/workouts/{id}` - Get single workout by ID
- `POST /api/v1/workouts` - Create new workout
- `PUT /api/v1/workouts/{id}` - Update workout metadata
- `DELETE /api/v1/workouts/{id}` - Delete workout

#### Analytics Endpoints
- `GET /api/v1/analytics/movements` - Movement usage statistics
- `GET /api/v1/analytics/equipment` - Equipment usage statistics
- `GET /api/v1/workouts/random` - Get random workouts

#### Utility Endpoints
- `GET /api/v1/schema` - Database schema info (for SQL queries)

## Implementation Tasks (Priority Focus)

### 1. Project Setup
- [ ] Add FastAPI and related dependencies to pyproject.toml
- [ ] Create `wodrag/api/` package structure
- [ ] Set up basic FastAPI application with CORS
- [ ] Add environment configuration for API settings

### 2. Pydantic Models (Search Only)
- [ ] Create `api/models/` package for request/response models
- [ ] Convert Workout dataclass to Pydantic BaseModel
- [ ] Create WorkoutFilter Pydantic model for query parameters
- [ ] Create SearchResult Pydantic model
- [ ] Create response models with pagination metadata

### 3. API Router Structure (Search Focus)
- [ ] Create `api/routers/` package for endpoint organization
- [ ] Implement `search.py` router for all search endpoints
- [ ] Implement `health.py` router for system status
- [ ] Implement `query.py` router for natural language queries

### 4. Service Layer Integration
- [ ] Create `api/dependencies.py` for dependency injection
- [ ] Create database connection dependency
- [ ] Create WorkoutRepository dependency
- [ ] Create EmbeddingService dependency  
- [ ] Create DuckDBQueryService dependency
- [ ] Add proper error handling and exception mapping

### 5. Search Endpoints Implementation
- [ ] Implement hybrid search endpoint with configurable weights
- [ ] Implement semantic search endpoint
- [ ] Implement BM25 text search endpoint
- [ ] Add query parameter validation and defaults
- [ ] Add result pagination and metadata
- [ ] Handle empty queries and error cases

### 6. Natural Language Query Endpoint
- [ ] Integrate DuckDBQueryService for read-only queries
- [ ] Add text-to-SQL conversion via DSPy agent
- [ ] Implement query execution with result formatting
- [ ] Add query validation and safety checks
- [ ] Include schema information in responses

### 7. Error Handling
- [ ] Create custom exception classes for API errors
- [ ] Implement global exception handlers
- [ ] Add structured error responses
- [ ] Include error codes and helpful messages
- [ ] Log errors appropriately

### 8. Documentation & OpenAPI
- [ ] Configure automatic OpenAPI schema generation
- [ ] Add comprehensive endpoint documentation
- [ ] Include example requests/responses
- [ ] Create API usage examples

### 9. Testing
- [ ] Create test client fixtures for FastAPI testing
- [ ] Write integration tests for search endpoints
- [ ] Test error conditions and edge cases
- [ ] Add performance tests for search endpoints

### 10. Configuration & Deployment
- [ ] Add API configuration via environment variables
- [ ] Create startup/shutdown event handlers
- [ ] Add health check endpoint with database connectivity
- [ ] Create API server script

## Maybe Later (Auth Required)

### CRUD Endpoints Implementation
- [ ] Implement workout listing with pagination
- [ ] Implement workout retrieval by ID
- [ ] Implement workout creation with validation
- [ ] Implement workout metadata updates
- [ ] Implement workout deletion
- [ ] Add proper HTTP status codes and error responses

### Analytics Endpoints Implementation
- [ ] Implement movement statistics endpoint
- [ ] Implement equipment statistics endpoint
- [ ] Implement random workout selection
- [ ] Add caching for expensive analytics queries
- [ ] Include metadata about statistics (total counts, etc.)

### Authentication & Security
- [ ] Implement API key authentication middleware
- [ ] Add rate limiting to prevent abuse
- [ ] Implement request/response logging
- [ ] Add input validation and sanitization
- [ ] Secure SQL query endpoint against injection

### Performance Optimization
- [ ] Add response caching for expensive operations
- [ ] Implement connection pooling
- [ ] Add async support where beneficial
- [ ] Optimize search result serialization
- [ ] Add query result streaming for large datasets

## API Design Decisions

### Response Format
All API responses will follow a consistent structure:
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1, 
    "page_size": 20,
    "has_next": true
  },
  "status": "success"
}
```

### Error Format
```json
{
  "error": {
    "code": "WORKOUT_NOT_FOUND",
    "message": "Workout with ID 123 not found",
    "details": {}
  },
  "status": "error"
}
```

### HTTP Methods
All search endpoints use GET since they are read-only operations:
- Search endpoints accept query parameters
- Natural language query endpoint accepts `q` parameter for the query text
- Results are cacheable and idempotent

### Authentication (Future)
- API key in `X-API-Key` header
- Simple validation against environment variable
- Future: JWT tokens for more complex auth

### Pagination
- Standard `page` and `page_size` query parameters
- Default page_size: 20, max: 100
- Include pagination metadata in responses

## File Structure (Phase 1)
```
wodrag/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── config.py            # API configuration
│   ├── dependencies.py      # Dependency injection
│   ├── exceptions.py        # Custom exceptions
│   ├── models/             
│   │   ├── __init__.py
│   │   ├── responses.py     # Response models
│   │   └── workouts.py      # Workout-related models
│   └── routers/
│       ├── __init__.py
│       ├── search.py        # Search endpoints
│       ├── health.py        # Health/status endpoints
│       └── query.py         # Natural language queries
└── scripts/
    └── run_api.py           # API server script
```

## Success Criteria

- [ ] All endpoints functional with proper error handling
- [ ] Comprehensive test coverage (>90%)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Auto-generated OpenAPI documentation
- [ ] Performance benchmarks for search endpoints
- [ ] Security validation (no SQL injection, proper auth)

## Out of Scope

- Frontend web application (future sprint)
- Advanced authentication (OAuth, JWT)
- Real-time features (WebSockets)
- GraphQL API
- Advanced caching (Redis)
- Containerized deployment configs