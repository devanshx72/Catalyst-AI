"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

export default function MentorshipPage() {
  const [statusMessage, setStatusMessage] = useState<string>("Under Development");

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await api.getMentorshipStatus();
        if (res?.message) {
          setStatusMessage(res.message);
        }
      } catch {
        // graceful fallback
      }
    }
    checkStatus();
  }, []);

  return (
    <div className="mentorship-card">
      <div className="mentorship-icon">🤝</div>
      <span className="mentorship-badge">Coming Soon</span>
      <h2>Industry Mentorship Program</h2>
      <p style={{ color: "var(--text-secondary, #94a3b8)", lineHeight: "1.6", margin: "1rem 0 2rem" }}>
        We are redesigning the 1-on-1 industry mentorship experience to match our new curriculum and AI coaching platform.
      </p>
      <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "1rem", borderRadius: "0.75rem", marginBottom: "2rem", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <span style={{ fontSize: "0.85rem", color: "#94a3b8" }}>Server Status: </span>
        <code style={{ color: "#38bdf8", fontSize: "0.85rem" }}>{statusMessage}</code>
      </div>
      <div>
        <Link href="/coach" className="coach-send-btn" style={{ textDecoration: "none", display: "inline-block" }}>
          Chat with AI Coach Leo instead →
        </Link>
      </div>
    </div>
  );
}
