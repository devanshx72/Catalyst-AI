"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import type { RegisterRequest } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  // Required Fields
  const [formData, setFormData] = useState<RegisterRequest>({
    username: "",
    name: "",
    email: "",
    phone: "",
    dob: "",
    password: "",
    confirm_password: "",
    // Optional Profile Fields
    joining_date: "",
    career_goal: "",
    entrepreneurship_interest: "",
    interested_industries: "",
    dream_company: "",
    company_preference: "",
    preferred_company: "",
    personal_statement: "",
    github_profile: "",
    linkedin_profile: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showOptionalFields, setShowOptionalFields] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Password strength calculation
  const calculateStrength = (pass: string): { score: number; text: string; color: string } => {
    if (!pass) return { score: 0, text: "Password strength indicator", color: "" };
    let score = 0;
    if (pass.length >= 6) score++;
    if (pass.length >= 10) score++;
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;

    if (score <= 2) return { score: 1, text: "Weak password", color: "weak" };
    if (score === 3) return { score: 2, text: "Medium password", color: "medium" };
    if (score === 4) return { score: 3, text: "Strong password", color: "strong" };
    return { score: 4, text: "Very Strong password", color: "strong" };
  };

  const strength = calculateStrength(formData.password);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Client check for password match
    if (formData.password !== formData.confirm_password) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    if (formData.password.length < 6) {
      setErrorMessage("Password must be at least 6 characters long.");
      return;
    }

    setIsSubmitting(true);

    try {
      // Clean empty strings for optional fields
      const payload: RegisterRequest = {
        username: formData.username.trim(),
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim(),
        dob: formData.dob,
        password: formData.password,
        confirm_password: formData.confirm_password,
      };

      if (formData.joining_date) payload.joining_date = formData.joining_date;
      if (formData.career_goal) payload.career_goal = formData.career_goal;
      if (formData.entrepreneurship_interest) payload.entrepreneurship_interest = formData.entrepreneurship_interest;
      if (formData.interested_industries) payload.interested_industries = formData.interested_industries;
      if (formData.dream_company) payload.dream_company = formData.dream_company;
      if (formData.company_preference) payload.company_preference = formData.company_preference;
      if (formData.preferred_company) payload.preferred_company = formData.preferred_company;
      if (formData.personal_statement) payload.personal_statement = formData.personal_statement;
      if (formData.github_profile) payload.github_profile = formData.github_profile;
      if (formData.linkedin_profile) payload.linkedin_profile = formData.linkedin_profile;

      await register(payload);
      router.push("/login?registered=true");
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err?.message || "Registration failed. Please check your inputs.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Left Branding Panel */}
      <div className="auth-branding">
        <div className="floating-shapes">
          <span />
          <span />
          <span />
        </div>
        <div className="glass-card">
          <div className="brand-icon">⚡</div>
          <h1>Join Catalyst AI</h1>
          <p>Start your journey to career success with AI-powered guidance and personalized learning paths.</p>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="auth-form-panel">
        <div className="auth-form-wrapper register-wrapper">
          <h2>Create Account</h2>
          <p className="subtitle">Fill in your details to get started</p>

          {errorMessage && (
            <div className="auth-alert error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {/* Username & Name Row */}
            <div className="form-row">
              <div className="form-floating">
                <span className="input-icon">@</span>
                <input
                  type="text"
                  className="form-control"
                  id="username"
                  name="username"
                  placeholder="Username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  autoComplete="username"
                />
              </div>
              <div className="form-floating">
                <span className="input-icon">👤</span>
                <input
                  type="text"
                  className="form-control"
                  id="name"
                  name="name"
                  placeholder="Full Name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* Email Field */}
            <div className="form-floating">
              <span className="input-icon">✉️</span>
              <input
                type="email"
                className="form-control"
                id="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
                autoComplete="email"
              />
            </div>

            {/* Phone & DOB Row */}
            <div className="form-row">
              <div className="form-floating">
                <span className="input-icon">📞</span>
                <input
                  type="tel"
                  className="form-control"
                  id="phone"
                  name="phone"
                  placeholder="Phone Number"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-floating">
                <span className="input-icon">📅</span>
                <input
                  type="date"
                  className="form-control"
                  id="dob"
                  name="dob"
                  value={formData.dob}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="form-floating">
              <span className="input-icon">🔒</span>
              <input
                type={showPassword ? "text" : "password"}
                className="form-control"
                id="password"
                name="password"
                placeholder="Password (min. 6 characters)"
                value={formData.password}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "👁️" : "👁️‍🗨️"}
              </button>
            </div>

            {/* Password Strength Indicator */}
            <div className="password-strength">
              {[1, 2, 3, 4].map((barIndex) => (
                <div
                  key={barIndex}
                  className={`strength-bar ${barIndex <= strength.score ? strength.color : ""}`}
                />
              ))}
            </div>
            <div className="strength-text">{strength.text}</div>

            {/* Confirm Password Field */}
            <div className="form-floating">
              <span className="input-icon">🛡️</span>
              <input
                type={showConfirmPassword ? "text" : "password"}
                className="form-control"
                id="confirm_password"
                name="confirm_password"
                placeholder="Confirm Password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              >
                {showConfirmPassword ? "👁️" : "👁️‍🗨️"}
              </button>
            </div>

            {/* Optional Career & Company Fields Toggle */}
            <div className="optional-toggle-container">
              <button
                type="button"
                className="optional-toggle-btn"
                onClick={() => setShowOptionalFields(!showOptionalFields)}
              >
                <span>{showOptionalFields ? "▼" : "▶"} Career &amp; Profile Preferences (Optional)</span>
              </button>
            </div>

            {showOptionalFields && (
              <div className="optional-fields-section">
                <div className="form-row">
                  <div className="form-floating">
                    <input
                      type="date"
                      className="form-control"
                      id="joining_date"
                      name="joining_date"
                      placeholder="Target Start Date"
                      value={formData.joining_date}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="career_goal"
                      name="career_goal"
                      placeholder="Career Goal (e.g. AI Engineer)"
                      value={formData.career_goal}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="dream_company"
                      name="dream_company"
                      placeholder="Dream Company"
                      value={formData.dream_company}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="preferred_company"
                      name="preferred_company"
                      placeholder="Preferred Company"
                      value={formData.preferred_company}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="company_preference"
                      name="company_preference"
                      placeholder="Company Preference (e.g. Startup, MNC)"
                      value={formData.company_preference}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="entrepreneurship_interest"
                      name="entrepreneurship_interest"
                      placeholder="Entrepreneurship Interest (Yes/No)"
                      value={formData.entrepreneurship_interest}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-floating">
                  <input
                    type="text"
                    className="form-control"
                    id="interested_industries"
                    name="interested_industries"
                    placeholder="Interested Industries (comma separated, e.g. Fintech, AI, Health)"
                    value={formData.interested_industries}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-row">
                  <div className="form-floating">
                    <input
                      type="url"
                      className="form-control"
                      id="github_profile"
                      name="github_profile"
                      placeholder="GitHub Profile URL"
                      value={formData.github_profile}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="form-floating">
                    <input
                      type="url"
                      className="form-control"
                      id="linkedin_profile"
                      name="linkedin_profile"
                      placeholder="LinkedIn Profile URL"
                      value={formData.linkedin_profile}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-floating">
                  <textarea
                    className="form-control textarea"
                    id="personal_statement"
                    name="personal_statement"
                    rows={3}
                    placeholder="Personal Statement / About You"
                    value={formData.personal_statement}
                    onChange={handleChange}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              className="btn-auth"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creating Account..." : "Create Account →"}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link href="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
