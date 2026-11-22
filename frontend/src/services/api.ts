import axios, { AxiosError } from 'axios';
import type {
  FactCheckRequest,
  FactCheckResponse,
  HealthResponse,
  ApiError,
} from '../types/factcheck';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // 90 seconds timeout for full multi-step live RAG verification
});

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const factCheckClaim = async (request: FactCheckRequest): Promise<FactCheckResponse> => {
  try {
    const response = await apiClient.post<FactCheckResponse>('/api/v1/fact-check', request);
    return response.data;
  } catch (err: unknown) {
    if (axios.isAxiosError(err)) {
      const axiosError = err as AxiosError<{ error?: string; detail?: unknown }>;
      const serverMessage =
        axiosError.response?.data?.error ||
        (typeof axiosError.response?.data?.detail === 'string'
          ? axiosError.response?.data?.detail
          : undefined);

      const errorPayload: ApiError = {
        message:
          serverMessage ||
          axiosError.message ||
          'Failed to verify claim. Please check backend connection.',
        status: axiosError.response?.status,
        details: axiosError.response?.data,
      };
      throw errorPayload;
    }
    const genericError: ApiError = {
      message: err instanceof Error ? err.message : 'An unexpected error occurred.',
    };
    throw genericError;
  }
};
