import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';

export default function AuthCallback() {
  const [, setLocation] = useLocation();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the session from Supabase (after OAuth redirect)
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          throw sessionError;
        }
        
        if (!session?.access_token) {
          throw new Error('No access token received');
        }
        
        // Call backend to create session and save user profile data
        const response = await fetch('http://localhost:5000/api/auth/supabase', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ accessToken: session.access_token }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to create session');
        }
        
        const data = await response.json();
        console.log('Auth successful:', data);
        
        // Redirect to chat on success
        setLocation('/chat');
      } catch (error) {
        console.error('Auth callback error:', error);
        // Redirect to login on error
        setLocation(`/login?error=${encodeURIComponent((error as any)?.message || 'Authentication failed')}`);
      }
    };

    handleCallback();
  }, [setLocation]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  );
}
