"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import api, { ApiError } from "@/lib/api";
import type { RoadmapResponse } from "@/types";

export default function RoadmapOverviewPage() {
  const { user } = useAuth();
  const [data, setData] = useState<RoadmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRoadmap = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getRoadmap();
      setData(res);
    } catch (err: any) {
      console.error("Failed to load roadmap:", err);
      setError(err.message || "Failed to load roadmap.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoadmap();
  }, []);

  const handleQuickGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await api.generateRoadmap(true);
      await loadRoadmap();
    } catch (err: any) {
      setError(err.message || "Failed to generate roadmap.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading your learning roadmap...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="page-error-card">
        <h3>Unable to load roadmap</h3>
        <p>{error}</p>
        <button
          type="button"
          className="btn-primary-action"
          onClick={() => window.location.reload()}
        >
          Try Again
        </button>
      </div>
    );
  }

  const hasCareerGoal = data?.has_career_goal ?? false;
  const hasRoadmap = data?.has_roadmap ?? false;
  const careerGoal = data?.career_goal || user?.career_goal || "";
  const phases = data?.roadmap_data?.phases || [];
  const version = data?.version || 1;
  const targetDuration = data?.target_duration_months || 6;
  const weeklyHours = data?.weekly_hours || 15;
  const valReport = data?.validation_report;
  const evalScore = data?.evaluation_score;
  const progressSummary = data?.progress_summary;

  return (
    <div className="roadmap-page-container">
      {/* Header */}
      <div className="roadmap-header-banner" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1>Learning &amp; Career Roadmap</h1>
          <p>
            {hasCareerGoal
              ? `Tailored curriculum for aspiring ${careerGoal}`
              : "Personalized step-by-step milestones to land your target role"}
          </p>
        </div>

        {hasRoadmap && (
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <Link
              href="/onboarding"
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "0.5rem",
                background: "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                color: "#fff",
                fontSize: "0.85rem",
                textDecoration: "none",
              }}
            >
              ⚙️ Re-align Goal / Upload Resume
            </Link>
          </div>
        )}
      </div>

      {error && (
        <div style={{ padding: "1rem", borderRadius: "0.5rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.4)", color: "#fca5a5", marginBottom: "1.5rem" }}>
          ⚠️ {error}
        </div>
      )}

      {/* State 1: No Career Goal Set */}
      {!hasCareerGoal && (
        <div className="roadmap-empty-state-card">
          <div className="empty-state-icon">🎯</div>
          <h2>Set Your Career Goal First!</h2>
          <p>
            To generate a personalized step-by-step learning roadmap, Catalyst AI needs to know
            your target role and career aspirations. Head over to guided onboarding to set your goal and upload your resume!
          </p>
          <div className="empty-state-actions">
            <Link href="/onboarding" className="btn-primary-action">
              Start Guided Onboarding →
            </Link>
          </div>
          <div className="empty-state-tip">
            <span>💡 <strong>Tip:</strong> Specify your weekly hours and learning duration for an adaptive workload.</span>
          </div>
        </div>
      )}

      {/* State 2: Career Goal Set but Roadmap Data Empty */}
      {hasCareerGoal && !hasRoadmap && (
        <div className="roadmap-empty-state-card">
          <div className="empty-state-icon">⏳</div>
          <h2>Roadmap Ready to Generate</h2>
          <p>
            Your career goal is set to <strong>&ldquo;{careerGoal}&rdquo;</strong>.
            Click below to run our AI curriculum planner, deterministic validator, and quality evaluator!
          </p>
          <div className="empty-state-actions" style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
            <button
              type="button"
              disabled={generating}
              onClick={handleQuickGenerate}
              className="btn-primary-action"
            >
              {generating ? "Synthesizing Curriculum..." : "🚀 Generate 4-Phase Roadmap"}
            </button>
            <Link href="/onboarding" className="btn-primary-action" style={{ background: "rgba(255, 255, 255, 0.1)" }}>
              Guided Onboarding &amp; Resume Upload →
            </Link>
          </div>
        </div>
      )}

      {/* State 3: Active Roadmap with Phases */}
      {hasRoadmap && phases.length > 0 && (
        <div className="phases-timeline">
          {/* Metadata & Quality Bar */}
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "1rem",
              background: "rgba(30, 41, 59, 0.6)",
              backdropFilter: "blur(8px)",
              padding: "1rem 1.25rem",
              borderRadius: "0.75rem",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              marginBottom: "1.5rem",
            }}
          >
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ fontSize: "0.85rem", background: "rgba(99, 102, 241, 0.2)", color: "#c7d2fe", padding: "0.25rem 0.6rem", borderRadius: "1rem", border: "1px solid rgba(99, 102, 241, 0.4)" }}>
                v{version} Active
              </span>
              <span style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
                ⏱️ {targetDuration} Months ({weeklyHours} hrs/week)
              </span>
              {valReport?.is_valid && (
                <span style={{ fontSize: "0.85rem", color: "#10b981", background: "rgba(16, 185, 129, 0.15)", padding: "0.25rem 0.6rem", borderRadius: "1rem" }}>
                  ✓ Schema &amp; Prerequisites Validated
                </span>
              )}
              {evalScore && (
                <span style={{ fontSize: "0.85rem", color: "#f59e0b", background: "rgba(245, 158, 11, 0.15)", padding: "0.25rem 0.6rem", borderRadius: "1rem" }}>
                  ⭐ Quality Score: {Math.round(evalScore.overall_score * 100)}%
                </span>
              )}
            </div>

            {progressSummary && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
                  Total Progress: {progressSummary.completed_tasks}/{progressSummary.total_tasks} tasks ({progressSummary.progress_percent}%)
                </span>
                <div style={{ width: 100, height: 8, background: "rgba(255, 255, 255, 0.1)", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${progressSummary.progress_percent}%`, height: "100%", background: "#10b981", transition: "width 0.3s" }} />
                </div>
              </div>
            )}
          </div>

          <div className="timeline-intro">
            <span>4-Phase Milestone Architecture</span>
          </div>

          <div className="phases-list">
            {phases.map((phase: any, index: number) => {
              let totalTasks = 0;
              let completedTasks = 0;

              if (phase.learning_plan?.weekly_schedule) {
                for (const week of phase.learning_plan.weekly_schedule) {
                  for (const task of week.daily_tasks || []) {
                    totalTasks++;
                    if (task.completed) completedTasks++;
                  }
                }
              }

              const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
              const isCompleted = totalTasks > 0 && completedTasks === totalTasks;
              const hasPlan = !!phase.learning_plan;

              const courses = phase.resources?.Courses || [];
              const books = phase.resources?.Books || [];
              const projects = phase.resources?.Projects || [];

              return (
                <div key={index} className={`phase-card ${isCompleted ? "phase-completed" : ""}`}>
                  <div className="phase-card-header">
                    <div className="phase-badge-group">
                      <span className="phase-number-badge">Phase {index + 1}</span>
                      {phase.duration && <span className="phase-duration-badge">⏱️ {phase.duration}</span>}
                      {isCompleted && <span className="phase-status-badge completed">Completed ✓</span>}
                    </div>
                    <h2 className="phase-name">{phase.name || `Phase ${index + 1}`}</h2>
                  </div>

                  {phase.description && (
                    <p className="phase-description">{phase.description}</p>
                  )}

                  {/* Skills tags */}
                  {Array.isArray(phase.skills) && phase.skills.length > 0 && (
                    <div className="phase-skills-section">
                      <strong>Target Skills:</strong>
                      <div className="skills-pill-row">
                        {phase.skills.map((skill: string, sIdx: number) => (
                          <span key={sIdx} className="skill-pill">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Curated Resources preview */}
                  {(courses.length > 0 || books.length > 0 || projects.length > 0) && (
                    <div className="phase-resources-preview">
                      {courses.length > 0 && (
                        <div className="resource-item">
                          <span className="resource-icon">🎓</span>
                          <span><strong>Course:</strong> {courses[0]}</span>
                        </div>
                      )}
                      {books.length > 0 && (
                        <div className="resource-item">
                          <span className="resource-icon">📖</span>
                          <span><strong>Book:</strong> {books[0]}</span>
                        </div>
                      )}
                      {projects.length > 0 && (
                        <div className="resource-item">
                          <span className="resource-icon">💻</span>
                          <span><strong>Project:</strong> {projects[0]}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Progress bar if learning plan exists */}
                  {hasPlan && (
                    <div className="phase-progress-container">
                      <div className="progress-info">
                        <span>Progress: {completedTasks}/{totalTasks} tasks</span>
                        <span>{progressPercent}%</span>
                      </div>
                      <div className="progress-track">
                        <div
                          className="progress-fill"
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Action Link to Phase Plan */}
                  <div className="phase-card-footer">
                    <Link
                      href={`/roadmap/${index}/plan`}
                      className={`btn-phase-action ${isCompleted ? "completed-btn" : ""}`}
                    >
                      {hasPlan
                        ? isCompleted
                          ? "Review Plan ✓"
                          : "Continue Learning Plan →"
                        : "View / Generate Learning Plan →"}
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
