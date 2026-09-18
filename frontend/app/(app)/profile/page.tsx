"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import api, { ApiError } from "@/lib/api";
import type { ProfileResponse, ProfileUpdateRequest } from "@/types";

export default function ProfilePage() {
  const { checkAuth } = useAuth();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("");
  const [joiningDate, setJoiningDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [careerGoal, setCareerGoal] = useState("");
  const [originalCareerGoal, setOriginalCareerGoal] = useState("");
  const [learningDuration, setLearningDuration] = useState("");
  const [learningDurationUnit, setLearningDurationUnit] = useState("months");
  const [dreamCompany, setDreamCompany] = useState("");
  const [preferredCompany, setPreferredCompany] = useState("");
  const [companyPreference, setCompanyPreference] = useState("");
  const [entrepreneurshipInterest, setEntrepreneurshipInterest] = useState("");
  const [interestedIndustries, setInterestedIndustries] = useState("");
  const [personalStatement, setPersonalStatement] = useState("");
  const [githubProfile, setGithubProfile] = useState("");
  const [linkedinProfile, setLinkedinProfile] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        const data = await api.getProfile();
        setProfile(data);
        setName(data.name || "");
        setPhone(data.phone || "");
        setDob(data.dob || "");
        setGender(data.gender || "");
        setJoiningDate(data.joining_date || "");
        setEndDate(data.enddate || "");
        setCareerGoal(data.career_goal || "");
        setOriginalCareerGoal(data.career_goal || "");
        setLearningDuration(data.learning_duration || "");
        setLearningDurationUnit(data.learning_duration_unit || "months");
        setDreamCompany(data.dream_company || "");
        setPreferredCompany(data.preferred_company || "");
        setCompanyPreference(data.company_preference || "");
        setEntrepreneurshipInterest(data.entrepreneurship_interest || "");
        setInterestedIndustries(
          data.interested_industries ||
            (Array.isArray(data.key_interests) ? data.key_interests.join(", ") : "")
        );
        setPersonalStatement(data.personal_statement || "");
        setGithubProfile(data.github_profile || "");
        setLinkedinProfile(data.linkedin_profile || "");
      } catch (err: any) {
        setErrorMessage(err.message || "Failed to load profile details");
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const hasCareerGoalChanged =
    originalCareerGoal.trim() !== "" &&
    careerGoal.trim().toLowerCase() !== originalCareerGoal.trim().toLowerCase();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setSaving(true);

    try {
      const payload: ProfileUpdateRequest = {
        name: name.trim(),
        phone: phone.trim() || undefined,
        dob: dob || undefined,
        gender: gender || undefined,
        joining_date: joiningDate || undefined,
        enddate: endDate || undefined,
        career_goal: careerGoal.trim() || undefined,
        learning_duration: learningDuration.trim() || undefined,
        learning_duration_unit: learningDurationUnit || "months",
        dream_company: dreamCompany.trim() || undefined,
        preferred_company: preferredCompany.trim() || undefined,
        company_preference: companyPreference.trim() || undefined,
        entrepreneurship_interest: entrepreneurshipInterest.trim() || undefined,
        interested_industries: interestedIndustries.trim() || undefined,
        personal_statement: personalStatement.trim() || undefined,
        github_profile: githubProfile.trim() || undefined,
        linkedin_profile: linkedinProfile.trim() || undefined,
      };

      const updated = await api.updateProfile(payload);
      setProfile(updated);
      setOriginalCareerGoal(updated.career_goal || "");
      await checkAuth(); // Refresh global auth state

      setSuccessMessage(
        hasCareerGoalChanged
          ? "Profile saved successfully! Your Career Goal was updated and active roadmap modules were reset."
          : "Profile updated successfully!"
      );
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err?.message || "Failed to save profile changes.");
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading your profile...</p>
      </div>
    );
  }

  return (
    <div className="profile-page-container">
      <div className="profile-header-banner">
        <div className="avatar-large">
          {name ? name.charAt(0).toUpperCase() : "U"}
        </div>
        <div className="profile-title-details">
          <h1>{name || "Student Profile"}</h1>
          <p className="profile-email-badge">📧 {profile?.email}</p>
          <span className="profile-role-badge">Student Member</span>
        </div>
      </div>

      {successMessage && (
        <div className="auth-alert success" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="auth-alert error" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Critical Active Modules Invalidation Notice */}
      {hasCareerGoalChanged && (
        <div className="warning-callout-card" role="alert">
          <div className="warning-icon">⚠️</div>
          <div className="warning-text">
            <strong>Active Roadmap Reset Warning</strong>
            <p>
              You are modifying your Career Goal from <em>&quot;{originalCareerGoal}&quot;</em> to{" "}
              <em>&quot;{careerGoal}&quot;</em>. Saving this change will automatically reset your active roadmap
              modules in the system so a new tailored curriculum can be generated.
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="profile-form">
        {/* Section 1: Personal Information */}
        <div className="form-card">
          <div className="card-header">
            <h2>Personal Information</h2>
            <p>Basic identifying details associated with your account</p>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                id="name"
                type="text"
                className="input-text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                className="input-text disabled"
                value={profile?.email || ""}
                disabled
                title="Email cannot be changed directly"
              />
              <span className="field-hint">Primary login identifier (read-only)</span>
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone Number</label>
              <input
                id="phone"
                type="tel"
                className="input-text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 234 567 8900"
              />
            </div>

            <div className="form-group">
              <label htmlFor="dob">Date of Birth</label>
              <input
                id="dob"
                type="date"
                className="input-text"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="gender">Gender</label>
              <select
                id="gender"
                className="input-select"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="joiningDate">Target Start Date</label>
              <input
                id="joiningDate"
                type="date"
                className="input-text"
                value={joiningDate}
                onChange={(e) => setJoiningDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Career Goals & Preferences */}
        <div className="form-card highlight-border">
          <div className="card-header">
            <h2>🎯 Career Aspirations &amp; Goals</h2>
            <p>Define your primary direction for personalized AI roadmaps</p>
          </div>

          <div className="form-group mb-4">
            <div className="label-with-badge">
              <label htmlFor="careerGoal">
                <strong>Target Career Goal *</strong>
              </label>
              <span className="info-badge">Key Roadmap Driver</span>
            </div>
            <input
              id="careerGoal"
              type="text"
              className={`input-text ${hasCareerGoalChanged ? "input-highlight" : ""}`}
              value={careerGoal}
              onChange={(e) => setCareerGoal(e.target.value)}
              placeholder="e.g. AI Engineer, Full Stack Developer, Data Scientist"
            />
            <span className="field-hint warning">
              💡 Notice: Updating your career goal unsets active learning modules to align with new objectives (manual-fixes #3).
            </span>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="learningDuration">Learning Duration</label>
              <div className="input-with-select">
                <input
                  id="learningDuration"
                  type="text"
                  className="input-text"
                  value={learningDuration}
                  onChange={(e) => setLearningDuration(e.target.value)}
                  placeholder="e.g. 3, 6, 12"
                />
                <select
                  className="input-select-addon"
                  value={learningDurationUnit}
                  onChange={(e) => setLearningDurationUnit(e.target.value)}
                >
                  <option value="months">Months</option>
                  <option value="weeks">Weeks</option>
                  <option value="years">Years</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="dreamCompany">Dream Company</label>
              <input
                id="dreamCompany"
                type="text"
                className="input-text"
                value={dreamCompany}
                onChange={(e) => setDreamCompany(e.target.value)}
                placeholder="e.g. Google, DeepMind, Stripe"
              />
            </div>

            <div className="form-group">
              <label htmlFor="preferredCompany">Preferred Company Category</label>
              <input
                id="preferredCompany"
                type="text"
                className="input-text"
                value={preferredCompany}
                onChange={(e) => setPreferredCompany(e.target.value)}
                placeholder="e.g. Tech Giants, Growth Startups"
              />
            </div>

            <div className="form-group">
              <label htmlFor="companyPreference">Company Culture Preference</label>
              <input
                id="companyPreference"
                type="text"
                className="input-text"
                value={companyPreference}
                onChange={(e) => setCompanyPreference(e.target.value)}
                placeholder="e.g. Remote, Hybrid, High Innovation"
              />
            </div>

            <div className="form-group">
              <label htmlFor="entrepreneurshipInterest">Entrepreneurship Interest</label>
              <select
                id="entrepreneurshipInterest"
                className="input-select"
                value={entrepreneurshipInterest}
                onChange={(e) => setEntrepreneurshipInterest(e.target.value)}
              >
                <option value="">Select interest</option>
                <option value="Yes">Yes, aspiring founder</option>
                <option value="Considering">Considering in the future</option>
                <option value="No">No, focused on industry employment</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="endDate">Target Completion Date</label>
              <input
                id="endDate"
                type="date"
                className="input-text"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 3: Professional Presence & Skills */}
        <div className="form-card">
          <div className="card-header">
            <h2>🌐 Professional Profiles &amp; Interests</h2>
            <p>Connect your external links for Leo Career Coach context</p>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="githubProfile">GitHub Profile URL</label>
              <input
                id="githubProfile"
                type="url"
                className="input-text"
                value={githubProfile}
                onChange={(e) => setGithubProfile(e.target.value)}
                placeholder="https://github.com/username"
              />
              <span className="field-hint">Used by Leo Coach to analyze public repositories</span>
            </div>

            <div className="form-group">
              <label htmlFor="linkedinProfile">LinkedIn Profile URL</label>
              <input
                id="linkedinProfile"
                type="url"
                className="input-text"
                value={linkedinProfile}
                onChange={(e) => setLinkedinProfile(e.target.value)}
                placeholder="https://linkedin.com/in/username"
              />
              <span className="field-hint">Your public professional profile URL</span>
            </div>
          </div>

          <div className="form-group mt-3">
            <label htmlFor="interestedIndustries">Interested Industries / Key Topics</label>
            <input
              id="interestedIndustries"
              type="text"
              className="input-text"
              value={interestedIndustries}
              onChange={(e) => setInterestedIndustries(e.target.value)}
              placeholder="e.g. Artificial Intelligence, Cloud Infrastructure, Fintech"
            />
            <span className="field-hint">Comma-separated topics for relevant feed recommendations</span>
          </div>

          <div className="form-group mt-3">
            <label htmlFor="personalStatement">Personal Statement / Bio</label>
            <textarea
              id="personalStatement"
              className="input-textarea"
              rows={4}
              value={personalStatement}
              onChange={(e) => setPersonalStatement(e.target.value)}
              placeholder="Brief summary of your background, motivations, and technical strengths..."
            />
          </div>
        </div>

        {/* Form Actions */}
        <div className="form-action-bar">
          <button
            type="submit"
            className="btn-primary-action"
            disabled={saving}
          >
            {saving ? "Saving Changes..." : "Save Profile Changes"}
          </button>
        </div>
      </form>
    </div>
  );
}
