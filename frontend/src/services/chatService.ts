import { api } from './api';

export interface Citation {
  source_type: string;
  source_id: string;
  repository_name?: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  answer: string;
  sources: Citation[];
  confidence: string;
  elapsed_time_seconds: number;
}

export const chatService = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', payload);
    return response.data;
  },
};
