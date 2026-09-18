"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";

function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const router = useRouter();
  const searchParams = useSearchParams();
  const registered = searchParams.get("registered");

  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({
        username: username.trim(),
        password,
      });
      router.push("/dashboard");
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err?.message || "An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Left Branding Panel */}
      <div className="auth-branding">
        <div className="floating-shapes">
          <span />
          <span />
          <span />
        </div>
        <div className="glass-card">
          <div className="brand-icon">⚡</div>
          <h1>Welcome Back!</h1>
          <p>Your AI-powered career readiness platform. Unlock your potential with personalized guidance.</p>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="auth-form-panel">
        <div className="auth-form-wrapper">
          <h2>Sign In</h2>
          <p className="subtitle">Enter your credentials to access your account</p>

          {registered && !errorMessage && (
            <div className="auth-alert success">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <span>Account created successfully. Please log in with your credentials.</span>
            </div>
          )}

          {errorMessage && (
            <div className="auth-alert error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-floating">
              <span className="input-icon">👤</span>
              <input
                type="text"
                className="form-control"
                id="username"
                name="username"
                placeholder="Username or Email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>

            <div className="form-floating">
              <span className="input-icon">🔒</span>
              <input
                type={showPassword ? "text" : "password"}
                className="form-control"
                id="password"
                name="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "👁️" : "👁️‍🗨️"}
              </button>
            </div>

            <button
              type="submit"
              className="btn-auth"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign In →"}
            </button>
          </form>

          <div className="auth-footer">
            Don&apos;t have an account? <Link href="/register">Create one</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="auth-loading-screen"><div className="spinner" /><p>Loading...</p></div>}>
      <LoginForm />
    </Suspense>
  );
}
