"use client";

import React, { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import api, { ApiError } from "@/lib/api";
import type { PhasePlanResponse, WeeklyScheduleItem, DailyTask } from "@/types";

export default function PhasePlanPage({ params }: { params: Promise<{ phaseId: string }> }) {
  const resolvedParams = use(params);
  const phaseId = parseInt(resolvedParams.phaseId, 10);
  const router = useRouter();

  const [planData, setPlanData] = useState<PhasePlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [planNotFound, setPlanNotFound] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [openWeeks, setOpenWeeks] = useState<Record<number, boolean>>({
    0: true,
    1: true,
    2: true,
    3: true,
  });

  const loadPlan = useCallback(async () => {
    if (isNaN(phaseId)) return;
    try {
      setLoading(true);
      setActionError(null);
      setPlanNotFound(false);
      const res = await api.getPhasePlan(phaseId);
      setPlanData(res);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 404) {
        // Plan doesn't exist yet per manual-fixes #4
        setPlanNotFound(true);
      } else {
        setActionError(err.message || "Failed to load phase plan.");
      }
    } finally {
      setLoading(false);
    }
  }, [phaseId]);

  useEffect(() => {
    loadPlan();
  }, [loadPlan]);

  const handleGeneratePlan = async () => {
    try {
      setGenerating(true);
      setActionError(null);
      const res = await api.generatePhasePlan(phaseId);
      setPlanData({
        phase_id: res.phase_id,
        phase_name: `Phase ${phaseId + 1}`,
        skills: [],
        learning_plan: res.learning_plan,
      });
      setPlanNotFound(false);
    } catch (err: any) {
      setActionError(err.message || "Failed to generate learning plan.");
    } finally {
      setGenerating(false);
    }
  };

  const handleTaskToggle = async (weekIndex: number, dayIndex: number, currentCompleted: boolean) => {
    if (!planData?.learning_plan?.weekly_schedule) return;

    const newCompleted = !currentCompleted;

    // 1. Optimistic UI update
    setPlanData((prev) => {
      if (!prev?.learning_plan?.weekly_schedule) return prev;
      const updatedSchedule = [...prev.learning_plan.weekly_schedule];
      const targetWeek = { ...updatedSchedule[weekIndex] };
      const targetTasks = [...targetWeek.daily_tasks];
      targetTasks[dayIndex] = { ...targetTasks[dayIndex], completed: newCompleted };
      targetWeek.daily_tasks = targetTasks;
      updatedSchedule[weekIndex] = targetWeek;

      return {
        ...prev,
        learning_plan: {
          ...prev.learning_plan,
          weekly_schedule: updatedSchedule,
        },
      };
    });

    // 2. Call backend API
    try {
      await api.completeTask({
        phase_id: phaseId,
        week_index: weekIndex,
        day_index: dayIndex,
        completed: newCompleted,
      });
    } catch (err: any) {
      console.error("Task completion update failed, reverting:", err);
      // Revert optimistic update
      setPlanData((prev) => {
        if (!prev?.learning_plan?.weekly_schedule) return prev;
        const updatedSchedule = [...prev.learning_plan.weekly_schedule];
        const targetWeek = { ...updatedSchedule[weekIndex] };
        const targetTasks = [...targetWeek.daily_tasks];
        targetTasks[dayIndex] = { ...targetTasks[dayIndex], completed: currentCompleted };
        targetWeek.daily_tasks = targetTasks;
        updatedSchedule[weekIndex] = targetWeek;

        return {
          ...prev,
          learning_plan: {
            ...prev.learning_plan,
            weekly_schedule: updatedSchedule,
          },
        };
      });
      setActionError("Failed to update task completion on server. Reverted.");
    }
  };

  const toggleWeekCollapse = (wIdx: number) => {
    setOpenWeeks((prev) => ({
      ...prev,
      [wIdx]: !prev[wIdx],
    }));
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading weekly learning plan...</p>
      </div>
    );
  }

  // State: Plan Not Found (404) -> Prompt to Generate
  if (planNotFound) {
    return (
      <div className="plan-page-container">
        <div className="plan-back-bar">
          <Link href="/roadmap" className="back-link">
            ← Back to Roadmap
          </Link>
        </div>

        <div className="roadmap-empty-state-card">
          <div className="empty-state-icon">📋</div>
          <h2>Learning Plan Not Generated Yet</h2>
          <p>
            The weekly curriculum schedule for <strong>Phase {phaseId + 1}</strong> has not been created yet.
            Generate your detailed 4-week daily task breakdown to start learning.
          </p>

          {actionError && (
            <div className="auth-alert error" style={{ maxWidth: "500px", margin: "1rem auto" }}>
              <span>{actionError}</span>
            </div>
          )}

          <div className="empty-state-actions">
            <button
              type="button"
              className="btn-primary-action"
              onClick={handleGeneratePlan}
              disabled={generating}
            >
              {generating ? "Generating AI Learning Plan..." : "⚡ Generate Learning Plan"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (actionError && !planData) {
    return (
      <div className="plan-page-container">
        <div className="plan-back-bar">
          <Link href="/roadmap" className="back-link">
            ← Back to Roadmap
          </Link>
        </div>
        <div className="page-error-card">
          <h3>Error loading plan</h3>
          <p>{actionError}</p>
          <button type="button" className="btn-primary-action" onClick={loadPlan}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const schedule: WeeklyScheduleItem[] = planData?.learning_plan?.weekly_schedule || [];

  // Calculate overall phase completion
  let totalTasks = 0;
  let completedTasks = 0;
  for (const week of schedule) {
    for (const task of week.daily_tasks || []) {
      totalTasks++;
      if (task.completed) completedTasks++;
    }
  }
  const overallPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="plan-page-container">
      {/* Navigation Top Bar */}
      <div className="plan-back-bar">
        <Link href="/roadmap" className="back-link">
          ← Back to All Phases
        </Link>
      </div>

      {/* Phase Banner */}
      <div className="phase-plan-header">
        <div className="phase-plan-meta">
          <span className="phase-tag">Phase {phaseId + 1} Milestone</span>
          <h1>{planData?.phase_name || `Phase ${phaseId + 1} Learning Plan`}</h1>
          {Array.isArray(planData?.skills) && planData.skills.length > 0 && (
            <div className="skills-pill-row">
              {planData.skills.map((skill, sIdx) => (
                <span key={sIdx} className="skill-pill light">
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Progress Display */}
        <div className="phase-progress-box">
          <div className="progress-number">{overallPercentage}%</div>
          <span className="progress-label">Phase Complete</span>
          <span className="progress-sub">
            {completedTasks} of {totalTasks} Tasks Done
          </span>
        </div>
      </div>

      {actionError && (
        <div className="auth-alert error">
          <span>{actionError}</span>
        </div>
      )}

      {/* Weekly Schedule Accordion */}
      <div className="weeks-container">
        {schedule.map((week, wIdx) => {
          const isOpen = openWeeks[wIdx] ?? true;
          const weekTasks = week.daily_tasks || [];
          const weekTotal = weekTasks.length;
          const weekCompleted = weekTasks.filter((t) => t.completed).length;
          const weekPercent = weekTotal > 0 ? Math.round((weekCompleted / weekTotal) * 100) : 0;

          return (
            <div key={wIdx} className="week-card">
              {/* Week Card Header */}
              <div
                className="week-card-header"
                onClick={() => toggleWeekCollapse(wIdx)}
              >
                <div className="week-header-left">
                  <span className="week-badge">Week {week.week || wIdx + 1}</span>
                  <span className="week-task-count">
                    {weekCompleted}/{weekTotal} tasks completed
                  </span>
                </div>
                <div className="week-header-right">
                  <Link
                    href={`/tutor/${phaseId}/${week.week || wIdx + 1}`}
                    className="btn-tutor-link"
                    onClick={(e) => e.stopPropagation()}
                    title="Launch interactive AI Tutor for this week"
                  >
                    🤖 Open AI Tutor →
                  </Link>
                  <span className={`week-progress-pill ${weekPercent === 100 ? "complete" : ""}`}>
                    {weekPercent}%
                  </span>
                  <span className={`accordion-chevron ${isOpen ? "open" : ""}`}>▾</span>
                </div>
              </div>

              {/* Week Body */}
              {isOpen && (
                <div className="week-card-body">
                  {/* Learning Objectives */}
                  {Array.isArray(week.learning_objectives) && week.learning_objectives.length > 0 && (
                    <div className="week-objectives">
                      <strong>🎯 Key Objectives:</strong>
                      <ul>
                        {week.learning_objectives.map((obj, oIdx) => (
                          <li key={oIdx}>{obj}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Daily Tasks List */}
                  <div className="daily-tasks-list">
                    <strong>📅 Daily Tasks &amp; Milestones:</strong>
                    {weekTasks.map((task: DailyTask, dIdx: number) => {
                      const isTaskDone = !!task.completed;
                      const taskText = Array.isArray(task.tasks) ? task.tasks.join("; ") : (task as any).task || "Daily Study";

                      return (
                        <div
                          key={dIdx}
                          className={`task-row ${isTaskDone ? "task-completed" : ""}`}
                        >
                          <label className="task-checkbox-container">
                            <input
                              type="checkbox"
                              checked={isTaskDone}
                              onChange={() => handleTaskToggle(wIdx, dIdx, isTaskDone)}
                            />
                            <span className="custom-checkmark" />
                          </label>

                          <div className="task-content">
                            <div className="task-title-line">
                              <span className="day-tag">Day {task.day || dIdx + 1}</span>
                              <span className="task-desc">{taskText}</span>
                            </div>

                            <div className="task-meta-line">
                              {task.duration_hours && (
                                <span className="meta-item">⏳ {task.duration_hours} hrs</span>
                              )}
                              {Array.isArray(task.resources) && task.resources.length > 0 && (
                                <span className="meta-item">🔗 {task.resources.join(", ")}</span>
                              )}
                            </div>
                          </div>

                          <span className={`task-status-pill ${isTaskDone ? "done" : "pending"}`}>
                            {isTaskDone ? "Done ✓" : "Pending"}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Assessment */}
                  {week.assessment && (
                    <div className="week-assessment-box">
                      <span className="assessment-icon">📝</span>
                      <div>
                        <strong>Weekly Assessment:</strong>
                        <p>{week.assessment}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
