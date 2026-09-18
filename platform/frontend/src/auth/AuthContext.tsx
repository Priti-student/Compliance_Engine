import { createContext, useContext, useEffect, useState } from "react";
import { api, clearToken, getToken, setToken } from "../api/client";
import type { TokenResponse, User } from "../types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  ready: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const restore = async () => {
      const t = getToken();
      if (!t) {
        setReady(true);
        return;
      }
      try {
        const me = await api<User>("/auth/me");
        setUser(me);
      } catch {
        clearToken();
        setTokenState(null);
      }
      setReady(true);
    };
    restore();

    const onUnauthorized = () => {
      setUser(null);
      setTokenState(null);
    };
    window.addEventListener("lmpc:unauthorized", onUnauthorized);
    return () => window.removeEventListener("lmpc:unauthorized", onUnauthorized);
  }, []);

  const login = async (username: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);
    const resp = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!resp.ok) {
      let detail = "Login failed";
      try {
        const data = await resp.json();
        detail = data.detail || detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    const body = (await resp.json()) as TokenResponse;
    setToken(body.access_token);
    setTokenState(body.access_token);
    setUser(body.user);
  };

  const logout = () => {
    clearToken();
    setTokenState(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}