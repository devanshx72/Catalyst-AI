"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import api, { ApiError } from "@/lib/api";
import type { LoginRequest, LoginResponse, ProfileResponse, RegisterRequest, RegisterResponse } from "@/types";

interface AuthContextType {
  user: ProfileResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<LoginResponse>;
  register: (data: RegisterRequest) => Promise<RegisterResponse>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<ProfileResponse | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<ProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  const checkAuth = useCallback(async (): Promise<ProfileResponse | null> => {
    try {
      const profile = await api.getProfile();
      setUser(profile);
      return profile;
    } catch (err: any) {
      setUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.login(data);
    await checkAuth();
    return response;
  };

  const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
    return await api.register(data);
  };

  const logout = async (): Promise<void> => {
    try {
      await api.logout();
    } catch (err) {
      console.warn("Logout error:", err);
    } finally {
      setUser(null);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
