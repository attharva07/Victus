import { ReactNode, createContext, useContext, useMemo, useState } from 'react';

type AuthContextType = {
  token: string | null;
  setToken: (token: string | null) => void;
  apiBaseUrl: string;
};

const DEFAULT_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const value = useMemo(
    () => ({ token, setToken, apiBaseUrl: DEFAULT_API_BASE_URL }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
