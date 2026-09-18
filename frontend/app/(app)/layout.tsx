"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import ShellLayout from "@/components/ShellLayout";

export default function AppProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="auth-loading-screen">
        <div className="spinner" />
        <p>Checking session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <ShellLayout>{children}</ShellLayout>;
}
