import React from "react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "var(--background, #0b0f19)",
      color: "var(--text-primary, #ffffff)",
      fontFamily: "system-ui, -apple-system, sans-serif",
      padding: "2rem",
      textAlign: "center"
    }}>
      <div style={{
        maxWidth: "500px",
        background: "var(--surface-card, #131722)",
        border: "1px solid var(--surface-border, rgba(255, 255, 255, 0.08))",
        borderRadius: "1.25rem",
        padding: "3rem 2rem",
        boxShadow: "0 20px 40px rgba(0,0,0,0.4)"
      }}>
        <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>🔍</div>
        <h1 style={{ fontSize: "2rem", margin: "0 0 0.5rem", fontWeight: 700 }}>404 - Page Not Found</h1>
        <p style={{ color: "var(--text-secondary, #94a3b8)", lineHeight: "1.6", margin: "0 0 2rem" }}>
          The path you are looking for does not exist or has been moved in the new Catalyst platform.
        </p>
        <Link
          href="/dashboard"
          style={{
            display: "inline-block",
            padding: "0.75rem 1.5rem",
            background: "#2563eb",
            color: "#ffffff",
            borderRadius: "0.5rem",
            textDecoration: "none",
            fontWeight: 600,
            transition: "opacity 0.2s"
          }}
        >
          Return to Dashboard →
        </Link>
      </div>
    </div>
  );
}
