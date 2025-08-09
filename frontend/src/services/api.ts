import { ApiResponse, AgentQueryRequest, AgentQueryResponse } from '../types/api';
import { WorkoutWithSimilar } from '../types/workout';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api/v1'  // In production, use relative URL (proxied)
  : 'http://localhost:8000/api/v1'; // In development, use full URL

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ApiService {
  private static instance: ApiService;

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      // Always try to parse the response body, even for error statuses
      const responseData = await response.json();
      
      if (!response.ok) {
        // Check if the backend sent an error message in the expected format
        if (responseData && responseData.error) {
          return {
            success: false,
            data: null,
            error: responseData.error,
          };
        }
        
        // Fallback to generic error if no message provided
        throw new ApiError(
          `HTTP error! status: ${response.status}`,
          response.status
        );
      }
      
      // Backend returns data in ApiResponse format already
      // So we can return it directly
      return responseData as ApiResponse<T>;
    } catch (error) {
      console.error('API request failed:', error);
      
      if (error instanceof ApiError) {
        return {
          success: false,
          data: null,
          error: error.message,
        };
      }
      
      // Network or other errors
      return {
        success: false,
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  public async queryAgent(request: AgentQueryRequest): Promise<ApiResponse<AgentQueryResponse>> {
    return this.makeRequest<AgentQueryResponse>('/agent/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  public async getWorkoutByDate(
    year: number,
    month: number,
    day: number,
    similarLimit = 5,
    embedding: 'summary' | 'workout' = 'summary',
  ): Promise<ApiResponse<WorkoutWithSimilar>> {
    const m = String(month).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    const qs = new URLSearchParams({ similar_limit: String(similarLimit), embedding }).toString();
    return this.makeRequest<WorkoutWithSimilar>(`/workouts/${year}/${m}/${d}?${qs}`);
  }
}

export const apiService = ApiService.getInstance();
