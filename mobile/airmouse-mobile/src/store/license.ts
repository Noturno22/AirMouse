import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@maouse/license';

export type LicenseTier = 'free' | 'mobile_pro';

interface LicenseState {
  tier: LicenseTier;
  status: 'loading' | 'ready' | 'error';
  hydrate: () => Promise<void>;
  unlockPro: () => Promise<void>;
  clear: () => Promise<void>;
}

export const useLicenseStore = create<LicenseState>((set) => ({
  tier: 'free',
  status: 'loading',
  hydrate: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      const tier: LicenseTier = raw === 'mobile_pro' ? 'mobile_pro' : 'free';
      set({ tier, status: 'ready' });
    } catch {
      set({ tier: 'free', status: 'ready' });
    }
  },
  unlockPro: async () => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, 'mobile_pro');
    } catch {
      // non-fatal: still unlock for this session
    }
    set({ tier: 'mobile_pro', status: 'ready' });
  },
  clear: async () => {
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
    } catch {
      // non-fatal
    }
    set({ tier: 'free', status: 'ready' });
  },
}));
