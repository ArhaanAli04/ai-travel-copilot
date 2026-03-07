import { useAuth } from '@clerk/react';
import { useEffect, useRef } from 'react';
import { setAuthToken, syncUser } from '../services/api';

const AuthSync = () => {
  const { isSignedIn,isLoaded, getToken } = useAuth();
  const synced = useRef(false);

  useEffect(() => {
     if (!isLoaded) return; 

    if (!isSignedIn) {
      setAuthToken(null);
      synced.current = false;
      return;
    }

    const init = async () => {
      // Get fresh Clerk JWT and inject into axios
      const token = await getToken();
      setAuthToken(token);

      // Sync user to DB only once per session
      if (!synced.current) {
        try {
          await syncUser();
          synced.current = true;
        } catch (e) {
          console.error('User sync failed:', e);
        }
      }
    };

    init();

    // Refresh token every 50 seconds (Clerk tokens expire in 60s)
    const interval = setInterval(async () => {
      const token = await getToken();
      setAuthToken(token);
    }, 50_000);

    return () => clearInterval(interval);
  }, [isSignedIn,isLoaded, getToken]);

  return null;
};

export default AuthSync;
