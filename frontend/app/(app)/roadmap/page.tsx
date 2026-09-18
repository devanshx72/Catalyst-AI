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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRoadmap() {
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
    }
    loadRoadmap();
  }, []);

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

  return (
    <div className="roadmap-page-container">
      {/* Header */}
      <div className="roadmap-header-banner">
        <h1>Learning &amp; Career Roadmap</h1>
        <p>
          {hasCareerGoal
            ? `Tailored curriculum for aspiring ${careerGoal}`
            : "Personalized step-by-step milestones to land your target role"}
        </p>
      </div>

      {/* State 1: No Career Goal Set */}
      {!hasCareerGoal && (
        <div className="roadmap-empty-state-card">
          <div className="empty-state-icon">🎯</div>
          <h2>Set Your Career Goal First!</h2>
          <p>
            To generate a personalized step-by-step learning roadmap, Catalyst AI needs to know
            your target role and career aspirations. Head over to your profile and set your goal!
          </p>
          <div className="empty-state-actions">
            <Link href="/profile" className="btn-primary-action">
              Set Career Goal in Profile →
            </Link>
          </div>
          <div className="empty-state-tip">
            <span>💡 <strong>Tip:</strong> You can also set your preferred learning duration (e.g. 6 months) for an adaptive timeline.</span>
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
            Save your profile preferences or review your learning duration to generate your 4-phase curriculum.
          </p>
          <div className="empty-state-actions">
            <Link href="/profile" className="btn-primary-action">
              Review Profile &amp; Preferences →
            </Link>
          </div>
        </div>
      )}

      {/* State 3: Active Roadmap with Phases */}
      {hasRoadmap && phases.length > 0 && (
        <div className="phases-timeline">
          <div className="timeline-intro">
            <span>4-Phase Milestone Architecture</span>
          </div>

          <div className="phases-list">
            {phases.map((phase: any, index: number) => {
              // Calculate completion progress if phase has learning_plan
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
