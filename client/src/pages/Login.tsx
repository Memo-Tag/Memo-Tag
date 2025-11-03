import { useState } from "react";
import { useLocation } from "wouter";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { APP_LOGO, APP_TITLE } from "@/const";
import { Activity, Mail, Lock, UserPlus, LogIn, AlertCircle } from "lucide-react";
import { useSupabaseAuth } from "@/contexts/SupabaseAuthContext";

export default function LoginPage() {
  const [, setLocation] = useLocation();
  const [mode, setMode] = useState<'login'|'register'>('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { signUpWithEmail, signInWithEmail, signInWithGoogle, getIdToken } = useSupabaseAuth();

  const handleOAuthSignIn = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const { data, error: authError } = await signInWithGoogle();
      
      if (authError) {
        throw authError;
      }
      
      // Get access token for backend verification
      const idToken = await getIdToken();
      
      if (!idToken) {
        throw new Error('Failed to get authentication token');
      }
      
      // Send token to backend for session creation
      await api.auth.supabaseAuth({ accessToken: idToken });
      
      // Redirect to chat on success
      const redirect = (new URLSearchParams(window.location.search).get('redirect')) || '/chat';
      window.location.href = redirect;
    } catch (e: any) {
      console.error('Google sign-in error:', e);
      setError(e?.message || 'Failed to sign in with Google');
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    setError(null);
    
    // Validation
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }
    
    if (mode === 'register' && !name) {
      setError('Name is required for registration');
      return;
    }
    
    setLoading(true);
    try {
      if (mode === 'register') {
        // Sign up with Supabase
        const { data, error: signUpError } = await signUpWithEmail(email, password, name);
        
        if (signUpError) {
          throw signUpError;
        }
        
        // Get access token
        const idToken = await getIdToken();
        if (idToken) {
          // Create backend session
          await api.auth.supabaseAuth({ accessToken: idToken });
        }
      } else {
        // Sign in with Supabase
        const { data, error: signInError } = await signInWithEmail(email, password);
        
        if (signInError) {
          throw signInError;
        }
        
        // Get access token
        const idToken = await getIdToken();
        if (idToken) {
          // Create backend session
          await api.auth.supabaseAuth({ accessToken: idToken });
        }
      }
      
      // on success redirect to chat
      const redirect = (new URLSearchParams(window.location.search).get('redirect')) || '/chat';
      window.location.href = redirect;
    } catch (e: any) {
      setError(e?.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      submit();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-blue-100">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setLocation('/')}>
            {APP_LOGO && (
              <img src={APP_LOGO} alt={APP_TITLE} className="h-8 w-8" />
            )}
            <span className="text-xl font-bold">{APP_TITLE}</span>
          </div>
          <Button variant="ghost" onClick={() => setLocation('/')}>
            Back to Home
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <Activity className="w-8 h-8 text-primary" />
              </div>
            </div>
            <CardTitle className="text-2xl text-center">
              {mode === 'login' ? 'Welcome Back' : 'Create Account'}
            </CardTitle>
            <CardDescription className="text-center">
              {mode === 'login' 
                ? 'Sign in to access your medical assistant' 
                : 'Join MedChat for personalized medical information'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {error && (
                <Alert variant="destructive" className="animate-fade-in">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {mode === 'register' && (
                <div className="space-y-2">
                  <Label htmlFor="name">
                    <div className="flex items-center gap-2">
                      <UserPlus className="w-4 h-4" />
                      Full Name
                    </div>
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    className="h-11"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Email
                  </div>
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">
                  <div className="flex items-center gap-2">
                    <Lock className="w-4 h-4" />
                    Password
                  </div>
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  className="h-11"
                />
              </div>

              <Button 
                onClick={submit} 
                className="w-full h-11 text-base" 
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {mode === 'login' ? 'Signing In...' : 'Creating Account...'}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {mode === 'login' ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                    {mode === 'login' ? 'Sign In' : 'Create Account'}
                  </div>
                )}
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or continue with
                  </span>
                </div>
              </div>

              {/* OAuth Providers */}
              <div className="grid grid-cols-3 gap-3">
                <Button
                  variant="outline"
                  className="h-11"
                  onClick={() => handleOAuthSignIn()}
                  disabled={loading}
                  title="Sign in with Google"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </Button>
                
                {/* Microsoft and Apple removed - Supabase handles OAuth differently */}
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
                  </span>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full h-11"
                onClick={() => {
                  setMode(mode === 'login' ? 'register' : 'login');
                  setError(null);
                }}
                disabled={loading}
              >
                {mode === 'login' ? 'Create New Account' : 'Sign In Instead'}
              </Button>

              <div className="text-center">
                <Button
                  variant="link"
                  className="text-sm text-muted-foreground"
                  onClick={() => setLocation('/chat')}
                >
                  Continue as Guest →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <footer className="border-t border-border py-4 bg-background/50">
        <div className="container text-center text-sm text-muted-foreground">
          <p>By signing in, you agree to our Terms of Service and Privacy Policy</p>
        </div>
      </footer>
    </div>
  );
}
