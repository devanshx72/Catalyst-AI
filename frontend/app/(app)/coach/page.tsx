"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import DOMPurify from "dompurify";
import { useAuth } from "@/hooks/useAuth";
import api, { ApiError } from "@/lib/api";
import type { CoachMessage } from "@/types";

export default function CareerCoachLeoPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<CoachMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [clearNotice, setClearNotice] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);

  const chatBottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = useCallback(async () => {
    try {
      setLoadingHistory(true);
      setErrorMessage(null);
      const res = await api.getCoachMessages();
      setMessages(res?.messages || []);
    } catch (err: any) {
      console.error("Failed to load coach messages:", err);
      setErrorMessage(err.message || "Failed to load conversation history with Leo.");
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || sending) return;

    const userText = inputQuery.trim();
    setInputQuery("");
    setErrorMessage(null);
    setClearNotice(null);
    setSending(true);

    // Optimistically add user turn to UI
    const pendingTurn: CoachMessage = {
      prompt: userText,
      response: "",
      raw_response: "",
      time: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, pendingTurn]);

    try {
      const result = await api.chatWithCoach(userText);
      // Backend returns full conversation or single turn with messages array
      if (result.messages && Array.isArray(result.messages)) {
        setMessages(result.messages);
      } else {
        // Update the last pending turn with Leo's response
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0) {
            updated[lastIdx] = {
              prompt: userText,
              response: result.response,
              raw_response: result.raw_response || result.response,
              time: new Date().toISOString(),
            };
          }
          return updated;
        });
      }
    } catch (err: any) {
      console.error("Failed to chat with Leo:", err);
      // Remove optimistic turn on error
      setMessages((prev) => prev.slice(0, -1));
      setErrorMessage(err.message || "Leo encountered an error while formulating advice.");
    } finally {
      setSending(false);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear your entire conversation history with Leo?")) {
      return;
    }

    try {
      setClearing(true);
      await api.clearCoachHistory();
      setMessages([]);
      setClearNotice("Conversation history with Leo has been cleared.");
      setTimeout(() => setClearNotice(null), 4000);
    } catch (err: any) {
      alert("Failed to clear history: " + err.message);
    } finally {
      setClearing(false);
    }
  };

  // Safe HTML sanitizer preventing XSS
  const renderSanitizedHtml = (dirtyHtml: string) => {
    if (typeof window === "undefined") {
      return { __html: dirtyHtml };
    }
    const clean = DOMPurify.sanitize(dirtyHtml, {
      ALLOWED_TAGS: [
        "p", "br", "b", "i", "em", "strong", "a", "ul", "ol", "li",
        "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "code", "pre", "hr", "span"
      ],
      ALLOWED_ATTR: ["href", "target", "rel", "class"],
    });
    return { __html: clean };
  };

  if (loadingHistory) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Connecting to Leo, your Career Coach...</p>
      </div>
    );
  }

  return (
    <div className="coach-page-container">
      {/* Header Banner */}
      <div className="coach-header">
        <div className="coach-title-group">
          <div className="coach-avatar-large">🦁</div>
          <div>
            <h1>Career Coach Leo</h1>
            <p>
              Hi <strong>{user?.name || "there"}</strong>! I am your AI Career Coach.
              I analyze your target career goals, GitHub projects, and aspirations to give actionable career guidance.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn-clear-coach"
          onClick={handleClearHistory}
          disabled={clearing || sending || messages.length === 0}
          title="Clear full conversation history"
        >
          🗑️ Clear Conversation
        </button>
      </div>

      {clearNotice && (
        <div className="auth-alert success">
          <span>{clearNotice}</span>
        </div>
      )}

      {errorMessage && (
        <div className="auth-alert error">
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="coach-chat-card">
        <div className="coach-messages-scroll">
          {messages.length === 0 && !sending && (
            <div className="coach-empty-state">
              <div className="empty-icon">🦁</div>
              <h3>Ready to level up your career?</h3>
              <p>
                Ask me about interview preparation, resume reviews, salary negotiation tips,
                or what projects to build next for your target role.
              </p>
              <div className="coach-sample-prompts">
                <button
                  type="button"
                  className="sample-chip"
                  onClick={() => setInputQuery("Based on my goal, what should I build this week to stand out?")}
                >
                  &ldquo;What project should I build this week to stand out?&rdquo;
                </button>
                <button
                  type="button"
                  className="sample-chip"
                  onClick={() => setInputQuery("How can I prepare for technical interviews at my dream company?")}
                >
                  &ldquo;How can I prepare for technical interviews at my dream company?&rdquo;
                </button>
                <button
                  type="button"
                  className="sample-chip"
                  onClick={() => setInputQuery("What are the key strengths and gaps in my technical portfolio?")}
                >
                  &ldquo;What are key strengths and gaps in my portfolio?&rdquo;
                </button>
              </div>
            </div>
          )}

          {/* Render Turns */}
          {messages.map((turn, index) => {
            const isLastTurn = index === messages.length - 1;
            const isPendingResponse = isLastTurn && sending && !turn.response;

            return (
              <div key={index} className="coach-turn-block">
                {/* User Prompt */}
                {turn.prompt && (
                  <div className="coach-message-row user-row">
                    <div className="coach-avatar user">👤</div>
                    <div className="coach-bubble user-bubble">
                      <p className="bubble-text">{turn.prompt}</p>
                      {turn.time && (
                        <span className="bubble-timestamp">
                          {new Date(turn.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Leo Response */}
                {turn.response ? (
                  <div className="coach-message-row assistant-row">
                    <div className="coach-avatar leo">🦁</div>
                    <div className="coach-bubble leo-bubble">
                      <div
                        className="leo-html-content"
                        dangerouslySetInnerHTML={renderSanitizedHtml(turn.response)}
                      />
                      {turn.time && (
                        <span className="bubble-timestamp">
                          {new Date(turn.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      )}
                    </div>
                  </div>
                ) : isPendingResponse ? (
                  /* Waiting State for Leo (Non-Streaming LLM Call) */
                  <div className="coach-message-row assistant-row">
                    <div className="coach-avatar leo">🦁</div>
                    <div className="coach-bubble leo-bubble thinking-bubble">
                      <div className="thinking-row">
                        <span className="thinking-badge">Leo is analyzing</span>
                        <div className="typing-dots">
                          <span className="dot" />
                          <span className="dot" />
                          <span className="dot" />
                        </div>
                      </div>
                      <p className="thinking-text">Reviewing your career profile, GitHub repositories, and goals...</p>
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="coach-input-bar">
          <input
            type="text"
            className="coach-input-field"
            placeholder={sending ? "Leo is thinking..." : "Ask Leo anything about your career path or preparation..."}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={sending}
          />
          <button
            type="submit"
            className="coach-send-btn"
            disabled={!inputQuery.trim() || sending}
          >
            {sending ? "Analyzing..." : "Ask Leo →"}
          </button>
        </form>
      </div>
    </div>
  );
}
