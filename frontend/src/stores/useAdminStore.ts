import { create } from 'zustand';

interface AdminState {
  isAuthenticated: boolean;
  isAdminLoading: boolean;
  adminEmail: string | null;
  setAuthenticated: (auth: boolean, email?: string | null) => void;
  setAdminLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAdminStore = create<AdminState>((set) => ({
  isAuthenticated: false,
  isAdminLoading: true,
  adminEmail: null,

  setAuthenticated: (auth, email = null) => {
    set({ isAuthenticated: auth, adminEmail: email, isAdminLoading: false });
  },

  setAdminLoading: (loading) => {
    set({ isAdminLoading: loading });
  },

  logout: () => {
    set({ isAuthenticated: false, adminEmail: null, isAdminLoading: false });
  },
}));
