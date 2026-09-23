"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import api, { ApiError } from "@/lib/api";
import type {
  GoalResponse,
  ResumeResponse,
  SkillGapResponse,
  RoadmapGenerateResponse,
} from "@/types";

type OnboardingStep = 1 | 2 | 3 | 4;

export default function OnboardingPage() {
  const router = useRouter();
  const { user, checkAuth } = useAuth();

  const [currentStep, setCurrentStep] = useState<OnboardingStep>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Goal & Availability State
  const [goalTitle, setGoalTitle] = useState(user?.career_goal || "Full Stack Developer");
  const [targetDuration, setTargetDuration] = useState<number>(6);
  const [weeklyHours, setWeeklyHours] = useState<number>(15);
  const [currentLevel, setCurrentLevel] = useState<string>("beginner");
  const [companyPreference, setCompanyPreference] = useState(user?.dream_company || "");

  // Step 2: Resume Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [resumeData, setResumeData] = useState<ResumeResponse | null>(null);
  const [uploadProgress, setUploadProgress] = useState(false);
  const [customSkillInput, setCustomSkillInput] = useState("");

  // Step 3: Skill Gap State
  const [skillGap, setSkillGap] = useState<SkillGapResponse | null>(null);

  // Step 4: Generation State & Pipeline Animation
  const [generationStage, setGenerationStage] = useState<number>(0);
  const generationSteps = [
    "Synthesizing profile and career aspirations...",
    "Extracting and normalizing technical skills...",
    "Building tailored 4-phase milestone curriculum...",
    "Running deterministic prerequisite & workload validator...",
    "Evaluating roadmap quality and finalizing plan...",
  ];

  // Load existing active goal or resume if available
  useEffect(() => {
    async function loadExisting() {
      try {
        const [existingGoal, existingResume] = await Promise.all([
          api.getActiveGoal().catch(() => null),
          api.getActiveResume().catch(() => null),
        ]);

        if (existingGoal) {
          setGoalTitle(existingGoal.goal_title);
          setTargetDuration(existingGoal.target_duration_months);
          setWeeklyHours(existingGoal.weekly_hours);
          setCurrentLevel(existingGoal.current_level);
        }

        if (existingResume) {
          setResumeData(existingResume);
        }
      } catch (err) {
        console.warn("Could not prefetch onboarding data:", err);
      }
    }
    loadExisting();
  }, []);

  // Handle Step 1 -> Step 2
  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.createGoal({
        goal_title: goalTitle,
        target_duration_months: targetDuration,
        weekly_hours: weeklyHours,
        current_level: currentLevel,
        company_preference: companyPreference || undefined,
      });
      await checkAuth();
      setCurrentStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to save career goal.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Step 2: File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setError(null);
    setUploadProgress(true);

    try {
      const res = await api.uploadResume(file);
      setResumeData(res);
    } catch (err: any) {
      setError(err.message || "Failed to parse resume file.");
    } finally {
      setUploadProgress(false);
    }
  };

  const handleAddSkill = () => {
    if (!customSkillInput.trim() || !resumeData) return;
    const updated = [...(resumeData.parsed_data.skills || []), customSkillInput.trim()];
    setResumeData({
      ...resumeData,
      parsed_data: {
        ...resumeData.parsed_data,
        skills: updated,
      },
    });
    setCustomSkillInput("");
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    if (!resumeData) return;
    const updated = resumeData.parsed_data.skills.filter((s) => s !== skillToRemove);
    setResumeData({
      ...resumeData,
      parsed_data: {
        ...resumeData.parsed_data,
        skills: updated,
      },
    });
  };

  // Handle Step 2 -> Step 3
  const handleProceedToGap = async () => {
    setError(null);
    setLoading(true);
    try {
      if (resumeData) {
        await api.updateParsedResume({
          skills: resumeData.parsed_data.skills,
        });
      }
      const gap = await api.getSkillGap();
      setSkillGap(gap);
      setCurrentStep(3);
    } catch (err: any) {
      setError(err.message || "Failed to analyze skill gap.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Step 3 -> Step 4 (Generate Roadmap)
  const handleGenerateRoadmap = async () => {
    setError(null);
    setCurrentStep(4);
    setGenerationStage(0);

    // Animate stages for user feedback
    const interval = setInterval(() => {
      setGenerationStage((prev) => (prev < generationSteps.length - 1 ? prev + 1 : prev));
    }, 900);

    try {
      await api.generateRoadmap(true);
      clearInterval(interval);
      setGenerationStage(generationSteps.length - 1);
      setTimeout(() => {
        router.push("/roadmap");
      }, 1000);
    } catch (err: any) {
      clearInterval(interval);
      setError(err.message || "Roadmap generation encountered an issue.");
    }
  };

  return (
    <div className="onboarding-page-container" style={{ maxWidth: 880, margin: "0 auto", padding: "2rem 1rem" }}>
      {/* Header & Steps Progress Bar */}
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Welcome to Your Career Blueprint 🚀
        </h1>
        <p style={{ color: "var(--text-secondary, #94a3b8)", fontSize: "1rem" }}>
          Let&apos;s build a personalized, validated learning roadmap aligned with your exact career target.
        </p>

        {/* Step Indicator */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "1rem",
            marginTop: "1.5rem",
          }}
        >
          {[
            { num: 1, label: "Goal & Schedule" },
            { num: 2, label: "Resume Intelligence" },
            { num: 3, label: "Skill Gap Analysis" },
            { num: 4, label: "Curriculum Activation" },
          ].map((s) => (
            <div
              key={s.num}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                opacity: currentStep === s.num ? 1 : currentStep > s.num ? 0.8 : 0.4,
                fontWeight: currentStep === s.num ? 700 : 500,
                color: currentStep === s.num ? "var(--accent-primary, #6366f1)" : "inherit",
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.85rem",
                  background:
                    currentStep > s.num
                      ? "#10b981"
                      : currentStep === s.num
                      ? "var(--accent-primary, #6366f1)"
                      : "rgba(255, 255, 255, 0.1)",
                  color: "#fff",
                }}
              >
                {currentStep > s.num ? "✓" : s.num}
              </div>
              <span style={{ fontSize: "0.9rem" }}>{s.label}</span>
              {s.num < 4 && <span style={{ color: "rgba(255, 255, 255, 0.2)", marginLeft: "0.5rem" }}>→</span>}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: "1rem",
            borderRadius: "0.5rem",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            color: "#fca5a5",
            marginBottom: "1.5rem",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* STEP 1: CAREER GOAL & AVAILABILITY */}
      {currentStep === 1 && (
        <div
          style={{
            background: "rgba(30, 41, 59, 0.7)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "1rem",
            padding: "2rem",
          }}
        >
          <h2 style={{ fontSize: "1.3rem", fontWeight: 600, marginBottom: "1.25rem" }}>
            Step 1: Define Your Target Role &amp; Schedule
          </h2>

          <form onSubmit={handleSaveGoal} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.9rem", marginBottom: "0.4rem", fontWeight: 500 }}>
                Target Career Role / Title
              </label>
              <input
                type="text"
                required
                value={goalTitle}
                onChange={(e) => setGoalTitle(e.target.value)}
                placeholder="e.g. Full Stack Developer, AI Engineer, Backend Developer"
                style={{
                  width: "100%",
                  padding: "0.75rem 1rem",
                  borderRadius: "0.5rem",
                  background: "rgba(15, 23, 42, 0.6)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "#fff",
                }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.9rem", marginBottom: "0.4rem", fontWeight: 500 }}>
                  Target Completion Duration
                </label>
                <select
                  value={targetDuration}
                  onChange={(e) => setTargetDuration(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "0.75rem 1rem",
                    borderRadius: "0.5rem",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                  }}
                >
                  <option value={3}>3 Months (Accelerated Bootcamp)</option>
                  <option value={6}>6 Months (Standard Pacing - Recommended)</option>
                  <option value={9}>9 Months (In-depth Mastery)</option>
                  <option value={12}>12 Months (Comprehensive Year)</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.9rem", marginBottom: "0.4rem", fontWeight: 500 }}>
                  Weekly Availability (Hours/Week)
                </label>
                <input
                  type="number"
                  min={4}
                  max={60}
                  value={weeklyHours}
                  onChange={(e) => setWeeklyHours(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "0.75rem 1rem",
                    borderRadius: "0.5rem",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                  }}
                />
                <span style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)" }}>
                  Estimated total effort: ~{Math.round(targetDuration * 4.33 * weeklyHours)} hours
                </span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.9rem", marginBottom: "0.4rem", fontWeight: 500 }}>
                  Current Experience Level
                </label>
                <select
                  value={currentLevel}
                  onChange={(e) => setCurrentLevel(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.75rem 1rem",
                    borderRadius: "0.5rem",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                  }}
                >
                  <option value="beginner">Beginner (Starting fresh / Basic syntax)</option>
                  <option value="intermediate">Intermediate (Built side projects / Know basics)</option>
                  <option value="advanced">Advanced (Experienced / Transitioning domain)</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.9rem", marginBottom: "0.4rem", fontWeight: 500 }}>
                  Target Dream Company (Optional)
                </label>
                <input
                  type="text"
                  value={companyPreference}
                  onChange={(e) => setCompanyPreference(e.target.value)}
                  placeholder="e.g. Google, Stripe, Startups"
                  style={{
                    width: "100%",
                    padding: "0.75rem 1rem",
                    borderRadius: "0.5rem",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem" }}>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary-action"
                style={{
                  padding: "0.75rem 1.75rem",
                  fontSize: "1rem",
                  fontWeight: 600,
                  borderRadius: "0.5rem",
                  cursor: "pointer",
                }}
              >
                {loading ? "Saving..." : "Continue to Resume Upload →"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* STEP 2: RESUME UPLOAD & REVIEW */}
      {currentStep === 2 && (
        <div
          style={{
            background: "rgba(30, 41, 59, 0.7)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "1rem",
            padding: "2rem",
          }}
        >
          <h2 style={{ fontSize: "1.3rem", fontWeight: 600, marginBottom: "0.5rem" }}>
            Step 2: Resume Intelligence &amp; Skill Extraction
          </h2>
          <p style={{ color: "var(--text-secondary, #94a3b8)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
            Upload your resume (PDF or TXT, max 5MB). Our parser extracts your technical skills, experience, and projects once—no repeated token consumption.
          </p>

          {/* Upload Dropzone */}
          <div
            style={{
              border: "2px dashed rgba(99, 102, 241, 0.4)",
              borderRadius: "0.75rem",
              padding: "2rem",
              textAlign: "center",
              background: "rgba(15, 23, 42, 0.4)",
              marginBottom: "1.5rem",
            }}
          >
            <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📄</div>
            <p style={{ fontWeight: 600, marginBottom: "0.25rem" }}>
              {selectedFile ? selectedFile.name : "Select or drag your resume file"}
            </p>
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)" }}>
              Supported formats: .pdf, .txt, .docx (Max 5MB)
            </span>

            <div style={{ marginTop: "1rem" }}>
              <label
                htmlFor="resume-file-input"
                style={{
                  padding: "0.6rem 1.25rem",
                  background: "var(--accent-primary, #6366f1)",
                  color: "#fff",
                  borderRadius: "0.5rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  display: "inline-block",
                }}
              >
                {uploadProgress ? "Analyzing..." : "Choose Resume File"}
              </label>
              <input
                id="resume-file-input"
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleFileUpload}
                style={{ display: "none" }}
              />
            </div>
          </div>

          {/* Extracted Skills Preview & Editing */}
          {resumeData && (
            <div style={{ marginTop: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600 }}>
                  Extracted Technical Skills ({resumeData.parsed_data.skills.length})
                </h3>
                <span style={{ fontSize: "0.8rem", color: "#10b981" }}>Parsed Successfully ✓</span>
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
                {resumeData.parsed_data.skills.map((skill, idx) => (
                  <span
                    key={idx}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      background: "rgba(99, 102, 241, 0.15)",
                      border: "1px solid rgba(99, 102, 241, 0.3)",
                      color: "#c7d2fe",
                      padding: "0.3rem 0.75rem",
                      borderRadius: "1rem",
                      fontSize: "0.85rem",
                    }}
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#94a3b8",
                        cursor: "pointer",
                        padding: 0,
                        fontSize: "0.9rem",
                      }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>

              {/* Add Custom Skill */}
              <div style={{ display: "flex", gap: "0.5rem", maxWidth: 350, marginBottom: "1.5rem" }}>
                <input
                  type="text"
                  placeholder="Add missing skill..."
                  value={customSkillInput}
                  onChange={(e) => setCustomSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  style={{
                    flex: 1,
                    padding: "0.5rem 0.75rem",
                    borderRadius: "0.4rem",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                    fontSize: "0.85rem",
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddSkill}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "0.4rem",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  Add
                </button>
              </div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1.5rem" }}>
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              style={{
                padding: "0.6rem 1.25rem",
                background: "transparent",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                color: "#fff",
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              ← Back
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={handleProceedToGap}
              className="btn-primary-action"
              style={{
                padding: "0.75rem 1.75rem",
                fontSize: "1rem",
                fontWeight: 600,
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              {loading ? "Analyzing..." : "Review Skill Gap →"}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: SKILL GAP ANALYSIS */}
      {currentStep === 3 && (
        <div
          style={{
            background: "rgba(30, 41, 59, 0.7)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "1rem",
            padding: "2rem",
          }}
        >
          <h2 style={{ fontSize: "1.3rem", fontWeight: 600, marginBottom: "0.5rem" }}>
            Step 3: Skill Gap Analysis vs. {skillGap?.goal_title || goalTitle}
          </h2>
          <p style={{ color: "var(--text-secondary, #94a3b8)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
            Our engine analyzed your background against industry job requirements for {goalTitle}. Here is your readiness breakdown:
          </p>

          {/* Acquired Skills */}
          <div style={{ marginBottom: "1.5rem" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#10b981", marginBottom: "0.5rem" }}>
              ✓ Acquired Core Skills ({skillGap?.acquired_skills.length || 0})
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {skillGap?.acquired_skills.map((s, idx) => (
                <span
                  key={idx}
                  style={{
                    background: "rgba(16, 185, 129, 0.15)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    color: "#6ee7b7",
                    padding: "0.3rem 0.75rem",
                    borderRadius: "1rem",
                    fontSize: "0.85rem",
                  }}
                >
                  ✓ {s}
                </span>
              ))}
            </div>
          </div>

          {/* Missing / High-Priority Skills */}
          <div style={{ marginBottom: "1.5rem" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#f59e0b", marginBottom: "0.5rem" }}>
              🎯 Target Skills to Master ({skillGap?.missing_skills.length || 0})
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {skillGap?.missing_skills.map((s, idx) => (
                <span
                  key={idx}
                  style={{
                    background: "rgba(245, 158, 11, 0.15)",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                    color: "#fcd34d",
                    padding: "0.3rem 0.75rem",
                    borderRadius: "1rem",
                    fontSize: "0.85rem",
                  }}
                >
                  ★ {s}
                </span>
              ))}
            </div>
          </div>

          {/* Recommended Learning Order */}
          {skillGap?.recommended_learning_order && skillGap.recommended_learning_order.length > 0 && (
            <div
              style={{
                background: "rgba(15, 23, 42, 0.5)",
                borderRadius: "0.5rem",
                padding: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem" }}>
                Topological Prerequisite Learning Sequence:
              </h4>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary, #94a3b8)" }}>
                {skillGap.recommended_learning_order.join(" → ")}
              </p>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1.5rem" }}>
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              style={{
                padding: "0.6rem 1.25rem",
                background: "transparent",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                color: "#fff",
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleGenerateRoadmap}
              className="btn-primary-action"
              style={{
                padding: "0.75rem 2rem",
                fontSize: "1rem",
                fontWeight: 600,
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              Generate Validated Roadmap 🚀
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: GENERATION PIPELINE */}
      {currentStep === 4 && (
        <div
          style={{
            background: "rgba(30, 41, 59, 0.7)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "1rem",
            padding: "3rem 2rem",
            textAlign: "center",
          }}
        >
          <div className="spinner" style={{ margin: "0 auto 1.5rem auto", width: 48, height: 48 }} />
          <h2 style={{ fontSize: "1.4rem", fontWeight: 600, marginBottom: "1rem" }}>
            Orchestrating Your Curriculum
          </h2>

          <div style={{ maxWidth: 500, margin: "0 auto", textAlign: "left" }}>
            {generationSteps.map((stepMsg, idx) => {
              const isDone = generationStage > idx;
              const isCurrent = generationStage === idx;
              return (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                    padding: "0.6rem 0",
                    opacity: isDone || isCurrent ? 1 : 0.3,
                    color: isDone ? "#10b981" : isCurrent ? "var(--accent-primary, #6366f1)" : "inherit",
                  }}
                >
                  <span style={{ fontSize: "1.1rem" }}>{isDone ? "✓" : isCurrent ? "⏳" : "○"}</span>
                  <span style={{ fontSize: "0.95rem", fontWeight: isCurrent ? 600 : 400 }}>{stepMsg}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
