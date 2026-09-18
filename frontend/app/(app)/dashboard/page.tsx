"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import api from "@/lib/api";
import type { HomeResponse } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<HomeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHome() {
      try {
        setLoading(true);
        const homeData = await api.getHome();
        setData(homeData);
      } catch (err: any) {
        console.error("Failed to load dashboard data:", err);
        setError(err.message || "Failed to load dashboard content");
      } finally {
        setLoading(false);
      }
    }
    loadHome();
  }, []);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading your dashboard feed...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="page-error-card">
        <h3>Unable to load dashboard</h3>
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

  const categories = data?.categories || [];
  const companies = data?.companies || [];
  const stories = data?.stories || [];

  return (
    <div className="dashboard-container">
      {/* Welcome Hero Banner */}
      <div className="dashboard-hero">
        <div className="hero-text">
          <h1>Welcome back, {user?.name || "Student"}! 🚀</h1>
          <p>
            {user?.career_goal
              ? `Targeting: ${user.career_goal}${user.dream_company ? ` at ${user.dream_company}` : ""}`
              : "Track your learning progress, campus opportunities, and tech updates."}
          </p>
        </div>
        <div className="hero-quick-links">
          <Link href="/roadmap" className="quick-link-btn">
            <span>🗺️ Roadmap</span>
          </Link>
          <Link href="/coach" className="quick-link-btn">
            <span>🤖 Leo Coach</span>
          </Link>
          <Link href="/profile" className="quick-link-btn">
            <span>👤 Profile</span>
          </Link>
        </div>
      </div>

      {/* Tech Topics / Categories Bar */}
      <section className="dashboard-section">
        <div className="section-header">
          <h2>Trending Topics &amp; Skills</h2>
          <span className="section-subtitle">Click any topic to explore curated articles</span>
        </div>
        <div className="categories-pill-row">
          {categories.map((category) => (
            <Link
              key={category}
              href={`/articles?q=${encodeURIComponent(category.toLowerCase())}`}
              className="category-pill"
            >
              #{category}
            </Link>
          ))}
        </div>
      </section>

      {/* Grid: Visiting Companies & Tech News */}
      <div className="dashboard-content-grid">
        {/* Visiting Companies Section */}
        <section className="dashboard-section">
          <div className="section-header">
            <h2>🏢 Visiting Companies</h2>
            <span className="section-subtitle">Recent and upcoming campus opportunities</span>
          </div>

          {companies.length === 0 ? (
            <div className="empty-content-box">
              <p>No company visit schedules recorded yet.</p>
            </div>
          ) : (
            <div className="companies-list">
              {companies.map((company, idx) => (
                <div key={company._id || company.id || idx} className="company-card">
                  <div className="company-header">
                    <h3>{company.name || company.company_name || "Partner Company"}</h3>
                    {company.visit_date && (
                      <span className="badge-date">
                        {new Date(company.visit_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <div className="company-details">
                    {company.role && (
                      <p><strong>Role:</strong> {company.role}</p>
                    )}
                    {company.package && (
                      <p><strong>Package:</strong> {company.package}</p>
                    )}
                    {company.eligibility && (
                      <p><strong>Eligibility:</strong> {company.eligibility}</p>
                    )}
                    {company.location && (
                      <p><strong>Location:</strong> {company.location}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Latest Medium Articles Section */}
        <section className="dashboard-section">
          <div className="section-header">
            <div className="header-with-link">
              <h2>📰 Latest Tech Stories</h2>
              <Link href="/articles" className="header-action-link">
                View all stories →
              </Link>
            </div>
            <span className="section-subtitle">Curated articles from top engineering publications</span>
          </div>

          {stories.length === 0 ? (
            <div className="empty-content-box">
              <p>No articles found at the moment.</p>
            </div>
          ) : (
            <div className="stories-list">
              {stories.slice(0, 5).map((story, idx) => {
                const title = story.title || "Technology Article";
                const link = story.url || story.link || `https://medium.com/search?q=${encodeURIComponent(title)}`;
                const subtitle = story.subtitle || story.description || "";
                const author = story.author || story.creator || (story.authors && story.authors[0]);

                return (
                  <article key={story.id || idx} className="story-card">
                    <div className="story-body">
                      <h3>
                        <a href={link} target="_blank" rel="noopener noreferrer">
                          {title}
                        </a>
                      </h3>
                      {subtitle && <p className="story-subtitle">{subtitle}</p>}
                      <div className="story-meta">
                        {author && <span>By {author}</span>}
                        {story.published_at && (
                          <span>{new Date(story.published_at).toLocaleDateString()}</span>
                        )}
                        {story.claps !== undefined && (
                          <span>👏 {story.claps}</span>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
