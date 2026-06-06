import { api } from './api';

export interface Slot {
  id: string;
  slot: string;
  is_booked: boolean;
  booked_by_name?: string;
  booked_by_email?: string;
}

export interface BookRequest {
  slot: string;
  name: string;
  email: string;
}

export const schedulingService = {
  async getAvailableSlots(): Promise<Slot[]> {
    const response = await api.get<Slot[]>('/scheduling/slots');
    return response.data;
  },

  async bookSlot(payload: BookRequest): Promise<{ message: string; slot: string }> {
    const response = await api.post<{ message: string; slot: string }>('/scheduling/book', payload);
    return response.data;
  },
};
