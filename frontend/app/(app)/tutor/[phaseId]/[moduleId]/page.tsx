"use client";

import React, { useEffect, useState, useRef, useCallback, use } from "react";
import Link from "next/link";
import api, { ApiError, streamTutorChat } from "@/lib/api";
import type { ChatMessage, ResourceResponse, TutorContextResponse } from "@/types";

type StreamStatus = "idle" | "waiting" | "streaming" | "error";
type ResourceTab = "youtube" | "papers" | "web";

export default function TutorModuleChatPage({
  params,
}: {
  params: Promise<{ phaseId: string; moduleId: string }>;
}) {
  const resolvedParams = use(params);
  const phaseId = parseInt(resolvedParams.phaseId, 10);
  const moduleId = parseInt(resolvedParams.moduleId, 10);

  // Context & Chat state
  const [context, setContext] = useState<TutorContextResponse | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loadingContext, setLoadingContext] = useState(true);
  const [contextError, setContextError] = useState<string | null>(null);

  // Streaming state
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("idle");
  const [currentStreamText, setCurrentStreamText] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);
  const [tokenCount, setTokenCount] = useState(0);

  // Resources state
  const [activeTab, setActiveTab] = useState<ResourceTab>("youtube");
  const [resources, setResources] = useState<Record<string, any>>({});
  const [loadingResources, setLoadingResources] = useState(false);

  // Clear history state
  const [clearing, setClearing] = useState(false);
  const [clearNotice, setClearNotice] = useState<string | null>(null);

  // Auto-scroll ref
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load context on mount
  const loadContext = useCallback(async () => {
    if (isNaN(phaseId) || isNaN(moduleId)) return;
    try {
      setLoadingContext(true);
      setContextError(null);
      const data = await api.getTutorContext(phaseId, moduleId);
      setContext(data);
      setChatHistory(data.chat_history || []);

      // Load resources for module topic
      if (data.topic) {
        fetchResources(data.topic, "all");
      }
    } catch (err: any) {
      console.error("Failed to load tutor context:", err);
      setContextError(err.message || "Failed to load tutor module context.");
    } finally {
      setLoadingContext(false);
    }
  }, [phaseId, moduleId]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, currentStreamText, streamStatus]);

  // Fetch topic resources
  const fetchResources = async (topic: string, type: string = "all") => {
    try {
      setLoadingResources(true);
      const res = await api.getTutorResources(topic, type);
      if (res?.resources) {
        setResources((prev) => ({ ...prev, ...res.resources }));
      }
    } catch (err) {
      console.debug("Resources fetch error:", err);
    } finally {
      setLoadingResources(false);
    }
  };

  const handleTabChange = (tab: ResourceTab) => {
    setActiveTab(tab);
    if (!resources[tab] && context?.topic) {
      fetchResources(context.topic, tab);
    }
  };

  // Send message and stream response
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || streamStatus === "waiting" || streamStatus === "streaming") {
      return;
    }

    const userPrompt = inputMessage.trim();
    setInputMessage("");
    setStreamError(null);
    setClearNotice(null);

    // 1. Append user message immediately
    const userMsg: ChatMessage = {
      role: "user",
      content: userPrompt,
      timestamp: new Date().toISOString(),
    };
    setChatHistory((prev) => [...prev, userMsg]);

    // 2. Initialize streaming state: "waiting" for first token
    setStreamStatus("waiting");
    setCurrentStreamText("");
    setTokenCount(0);

    let accumulatedText = "";

    try {
      await streamTutorChat(
        phaseId,
        moduleId,
        userPrompt,
        // onToken callback
        (token: string) => {
          accumulatedText += token;
          setStreamStatus("streaming");
          setTokenCount((count) => count + 1);
          setCurrentStreamText(accumulatedText);
        },
        // onDone callback
        () => {
          setStreamStatus("idle");
          if (accumulatedText.trim()) {
            const assistantMsg: ChatMessage = {
              role: "assistant",
              content: accumulatedText.trim(),
              timestamp: new Date().toISOString(),
            };
            setChatHistory((prev) => [...prev, assistantMsg]);
          }
          setCurrentStreamText("");
          setTokenCount(0);
        },
        // onError callback
        (err: any) => {
          console.error("Stream error in component:", err);
          setStreamStatus("error");
          setStreamError(err.message || "Failed while streaming response from AI Tutor.");
        }
      );
    } catch (err: any) {
      console.error("Failed to start tutor chat stream:", err);
      setStreamStatus("error");
      setStreamError(err.message || "Unable to initiate chat stream.");
    }
  };

  // Clear Chat History
  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear the chat history for this module?")) {
      return;
    }

    try {
      setClearing(true);
      await api.clearTutorHistory(phaseId, moduleId);
      setChatHistory([]);
      setCurrentStreamText("");
      setStreamStatus("idle");
      setClearNotice("Chat history has been cleared.");
      setTimeout(() => setClearNotice(null), 4000);
    } catch (err: any) {
      alert("Failed to clear chat history: " + err.message);
    } finally {
      setClearing(false);
    }
  };

  if (loadingContext) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading AI Tutor session...</p>
      </div>
    );
  }

  if (contextError && !context) {
    return (
      <div className="tutor-container">
        <div className="plan-back-bar">
          <Link href={`/roadmap/${phaseId}/plan`} className="back-link">
            ← Back to Learning Plan
          </Link>
        </div>
        <div className="page-error-card">
          <h3>Failed to load Tutor Context</h3>
          <p>{contextError}</p>
          <button type="button" className="btn-primary-action" onClick={loadContext}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const topicTitle = context?.topic || `Phase ${phaseId + 1} - Week ${moduleId}`;
  const objectives = context?.objectives || [];
  const skills = context?.skills || [];
  const currentVideos = resources.youtube || [];
  const currentPapers = resources.papers || [];
  const currentWeb = resources.web || [];

  return (
    <div className="tutor-container">
      {/* Top Breadcrumb Navigation */}
      <div className="tutor-nav-bar">
        <Link href={`/roadmap/${phaseId}/plan`} className="back-link">
          ← Back to Week Schedule
        </Link>
        <div className="module-breadcrumbs">
          <span>Phase {phaseId + 1}</span>
          <span className="sep">/</span>
          <span>Week {moduleId} Tutor</span>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="tutor-layout-grid">
        {/* Left Column: Module Context & Learning Resources */}
        <aside className="tutor-context-panel">
          {/* Module Information Card */}
          <div className="tutor-card context-info-card">
            <div className="tutor-card-header">
              <span className="card-tag">Interactive AI Tutor</span>
              <h2>{topicTitle}</h2>
            </div>

            {objectives.length > 0 && (
              <div className="context-section">
                <strong>🎯 Learning Objectives:</strong>
                <ul>
                  {objectives.map((obj, idx) => (
                    <li key={idx}>{obj}</li>
                  ))}
                </ul>
              </div>
            )}

            {skills.length > 0 && (
              <div className="context-section">
                <strong>🛠️ Core Skills:</strong>
                <div className="skills-pill-row">
                  {skills.map((skill, idx) => (
                    <span key={idx} className="skill-pill">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Educational Resources Panel with Tabs */}
          <div className="tutor-card resources-card">
            <div className="resources-header">
              <h3>📚 Learning Resources</h3>
              <span className="resources-sub">Supplemental study material</span>
            </div>

            {/* Resource Type Tabs */}
            <div className="resource-tabs-nav">
              <button
                type="button"
                className={`resource-tab-btn ${activeTab === "youtube" ? "active" : ""}`}
                onClick={() => handleTabChange("youtube")}
              >
                🎥 Videos ({currentVideos.length})
              </button>
              <button
                type="button"
                className={`resource-tab-btn ${activeTab === "papers" ? "active" : ""}`}
                onClick={() => handleTabChange("papers")}
              >
                📄 Scholar ({currentPapers.length})
              </button>
              <button
                type="button"
                className={`resource-tab-btn ${activeTab === "web" ? "active" : ""}`}
                onClick={() => handleTabChange("web")}
              >
                🌐 Web ({currentWeb.length})
              </button>
            </div>

            {/* Tab Content */}
            <div className="resource-tab-content">
              {loadingResources ? (
                <div className="resource-loading">
                  <div className="spinner small" />
                  <span>Loading resources...</span>
                </div>
              ) : activeTab === "youtube" ? (
                currentVideos.length === 0 ? (
                  <p className="empty-tab-text">No video tutorials found for this topic.</p>
                ) : (
                  <div className="resource-items-list">
                    {currentVideos.map((vid: any, i: number) => (
                      <a
                        key={vid.id || i}
                        href={vid.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="resource-item-link"
                      >
                        <div className="resource-bullet">▶</div>
                        <div className="resource-info">
                          <p className="res-title">{vid.title}</p>
                          {vid.channelTitle && (
                            <span className="res-meta">{vid.channelTitle}</span>
                          )}
                        </div>
                      </a>
                    ))}
                  </div>
                )
              ) : activeTab === "papers" ? (
                currentPapers.length === 0 ? (
                  <p className="empty-tab-text">No academic publications found.</p>
                ) : (
                  <div className="resource-items-list">
                    {currentPapers.map((paper: any, i: number) => (
                      <a
                        key={i}
                        href={paper.url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="resource-item-link"
                      >
                        <div className="resource-bullet">📑</div>
                        <div className="resource-info">
                          <p className="res-title">{paper.title}</p>
                          {paper.snippet && (
                            <span className="res-meta">{paper.snippet}</span>
                          )}
                        </div>
                      </a>
                    ))}
                  </div>
                )
              ) : (
                currentWeb.length === 0 ? (
                  <p className="empty-tab-text">No web articles indexed.</p>
                ) : (
                  <div className="resource-items-list">
                    {currentWeb.map((site: any, i: number) => (
                      <a
                        key={i}
                        href={site.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="resource-item-link"
                      >
                        <div className="resource-bullet">🔗</div>
                        <div className="resource-info">
                          <p className="res-title">{site.title}</p>
                          {site.snippet && (
                            <span className="res-meta">{site.snippet}</span>
                          )}
                        </div>
                      </a>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        </aside>

        {/* Right Column: Interactive Chat Interface */}
        <section className="tutor-chat-panel">
          {/* Chat Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="tutor-avatar">🤖</div>
              <div>
                <h3>AI Tutor Assistant</h3>
                <span className="tutor-status-line">
                  {streamStatus === "streaming"
                    ? "● Streaming response..."
                    : streamStatus === "waiting"
                    ? "○ Thinking..."
                    : "Ready to help you master this module"}
                </span>
              </div>
            </div>

            <button
              type="button"
              className="clear-chat-btn"
              onClick={handleClearHistory}
              disabled={clearing || streamStatus !== "idle"}
              title="Clear message history for this module"
            >
              🗑️ Clear History
            </button>
          </div>

          {clearNotice && (
            <div className="auth-alert success" style={{ margin: "0.75rem 1.25rem 0" }}>
              <span>{clearNotice}</span>
            </div>
          )}

          {/* Messages Scroll Area */}
          <div className="chat-messages-container">
            {chatHistory.length === 0 && streamStatus === "idle" && (
              <div className="chat-empty-greeting">
                <div className="greeting-icon">💡</div>
                <h4>Hello! Ask me anything about this module</h4>
                <p>
                  I can explain complex concepts, give code examples, quiz your understanding,
                  or recommend step-by-step guidance for your daily tasks.
                </p>
                <div className="sample-prompts">
                  <button
                    type="button"
                    className="sample-prompt-chip"
                    onClick={() => setInputMessage("Can you summarize the core goals for this week?")}
                  >
                    &ldquo;Can you summarize the core goals for this week?&rdquo;
                  </button>
                  <button
                    type="button"
                    className="sample-prompt-chip"
                    onClick={() => setInputMessage("Give me a hands-on exercise to practice.")}
                  >
                    &ldquo;Give me a hands-on exercise to practice.&rdquo;
                  </button>
                </div>
              </div>
            )}

            {/* Historical and current messages */}
            {chatHistory.map((msg, index) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={index}
                  className={`chat-message-row ${isUser ? "user-row" : "assistant-row"}`}
                >
                  <div className="message-avatar">
                    {isUser ? "👤" : "🤖"}
                  </div>
                  <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
                    <p className="message-text">{msg.content}</p>
                    {msg.timestamp && (
                      <span className="message-timestamp">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Waiting State: Waiting for first token */}
            {streamStatus === "waiting" && (
              <div className="chat-message-row assistant-row">
                <div className="message-avatar">🤖</div>
                <div className="message-bubble assistant-bubble waiting-bubble">
                  <div className="waiting-indicator">
                    <span className="pulsing-badge">Thinking</span>
                    <span className="typing-dots">
                      <span className="dot" />
                      <span className="dot" />
                      <span className="dot" />
                    </span>
                  </div>
                  <p className="waiting-text">AI Tutor is formulating your response...</p>
                </div>
              </div>
            )}

            {/* Streaming State: Incrementally arriving tokens */}
            {streamStatus === "streaming" && (
              <div className="chat-message-row assistant-row">
                <div className="message-avatar">🤖</div>
                <div className="message-bubble assistant-bubble streaming-bubble">
                  <div className="streaming-badge-row">
                    <span className="live-stream-badge">
                      ● Live Stream ({tokenCount} tokens)
                    </span>
                  </div>
                  <p className="message-text">
                    {currentStreamText}
                    <span className="streaming-cursor">▌</span>
                  </p>
                </div>
              </div>
            )}

            {/* Error state */}
            {streamStatus === "error" && (
              <div className="stream-error-notice">
                <span>⚠️ {streamError || "Streaming interrupted. Please try again."}</span>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* Message Input Bar */}
          <form onSubmit={handleSendMessage} className="chat-input-bar">
            <input
              type="text"
              className="chat-input-field"
              placeholder={
                streamStatus === "waiting" || streamStatus === "streaming"
                  ? "AI Tutor is typing..."
                  : "Type a question or ask for an explanation..."
              }
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={streamStatus === "waiting" || streamStatus === "streaming"}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={
                !inputMessage.trim() ||
                streamStatus === "waiting" ||
                streamStatus === "streaming"
              }
            >
              {streamStatus === "waiting" || streamStatus === "streaming" ? (
                "..."
              ) : (
                "Send →"
              )}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
