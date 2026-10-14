import { AppState } from 'react-native';
import { createClient } from '@supabase/supabase-js';
import { secureChunkedStorage } from './secureStorage';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase config missing (EXPO_PUBLIC_SUPABASE_*)');
}

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    storage: secureChunkedStorage,
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: false,
  },
});

AppState.addEventListener('change', (state) => {
  if (state === 'active') {
    supabase.auth.startAutoRefresh();
  } else {
    supabase.auth.stopAutoRefresh();
  }
});