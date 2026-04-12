import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

/**
 * Zairyx IA | Padrão Store (Zustand + Immer + Persist) 
 * Herdado do Cardápio Digital: Mutações .set() com drafts mutáveis.
 */

export interface ZairyxUser {
  id: string;
  email: string;
  fullName: string;
  subscriptionPlan: 'FREE' | 'PREMIUM' | 'ENTERPRISE';
}

interface UserState {
  user: ZairyxUser | null;
  isAuthenticated: boolean;
}

interface UserActions {
  setUser: (user: ZairyxUser | null) => void;
  upgradePlan: (newPlan: ZairyxUser['subscriptionPlan']) => void;
  logout: () => void;
}

type UserStore = UserState & UserActions;

export const useUserStore = create<UserStore>()(
  persist(
    immer((set) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user) => 
        set((state) => {
          state.user = user;
          state.isAuthenticated = !!user;
        }),

      upgradePlan: (newPlan) =>
        set((state) => {
          if (state.user) {
            state.user.subscriptionPlan = newPlan;
          }
        }),

      logout: () =>
        set((state) => {
          state.user = null;
          state.isAuthenticated = false;
        }),
    })),
    {
      name: 'zairyx-auth-storage', // Chave do localStorage
      // partialize: (state) => ({ user: state.user }) // Opcional se quiser persistir só dados específicos
    }
  ) // Fechando persist()
);