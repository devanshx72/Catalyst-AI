"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import api, { ApiError } from "@/lib/api";
import type { ArticlesResponse } from "@/types";

function ArticlesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialQuery = searchParams.get("q") || "technology";
  const [query, setQuery] = useState(initialQuery);
  const [searchInput, setSearchInput] = useState(initialQuery);
  const [page, setPage] = useState(0);

  const [data, setData] = useState<ArticlesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticles = useCallback(async (searchQuery: string, pageNumber: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getArticles(searchQuery, pageNumber);
      setData(res);
    } catch (err: any) {
      console.error("Failed to fetch articles:", err);
      setError(err.message || "Failed to load articles for this topic.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = searchParams.get("q") || "technology";
    setQuery(q);
    setSearchInput(q);
    setPage(0);
    fetchArticles(q, 0);
  }, [searchParams, fetchArticles]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    const trimmed = searchInput.trim();
    setQuery(trimmed);
    setPage(0);
    router.push(`/articles?q=${encodeURIComponent(trimmed)}`);
  };

  const handleCategoryClick = (cat: string) => {
    const lower = cat.toLowerCase();
    setQuery(lower);
    setSearchInput(lower);
    setPage(0);
    router.push(`/articles?q=${encodeURIComponent(lower)}`);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage < 0) return;
    setPage(newPage);
    fetchArticles(query, newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const categories = data?.categories || [];
  const stories = data?.stories || [];

  return (
    <div className="articles-page-container">
      {/* Header */}
      <div className="articles-header">
        <h1>Tech News &amp; Articles</h1>
        <p>Explore engineering blogs, AI developments, and industry insights</p>
      </div>

      {/* Search Input Bar */}
      <div className="articles-search-bar">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <input
            type="text"
            className="search-input"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search tech topics (e.g., Python, React, Machine Learning)..."
          />
          <button type="submit" className="btn-primary-action">
            Search
          </button>
        </form>
      </div>

      {/* Categories Filter Pills */}
      {categories.length > 0 && (
        <div className="categories-pill-row scrollable">
          {categories.map((cat) => {
            const isSelected = query.toLowerCase() === cat.toLowerCase();
            return (
              <button
                key={cat}
                type="button"
                className={`category-pill ${isSelected ? "selected" : ""}`}
                onClick={() => handleCategoryClick(cat)}
              >
                #{cat}
              </button>
            );
          })}
        </div>
      )}

      {/* Search Status Header */}
      <div className="articles-status-banner">
        <span>
          Showing results for <strong>&ldquo;{query}&rdquo;</strong> (Page {page + 1})
        </span>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="page-loading">
          <div className="spinner" />
          <p>Fetching latest articles...</p>
        </div>
      ) : error ? (
        <div className="page-error-card">
          <h3>Failed to load articles</h3>
          <p>{error}</p>
          <button
            type="button"
            className="btn-primary-action"
            onClick={() => fetchArticles(query, page)}
          >
            Retry
          </button>
        </div>
      ) : stories.length === 0 ? (
        <div className="empty-content-box">
          <p>No stories found for &ldquo;{query}&rdquo;. Try another keyword or topic.</p>
        </div>
      ) : (
        <div className="articles-list-grid">
          {stories.map((story, idx) => {
            const title = story.title || "Technology Article";
            const link = story.url || story.link || `https://medium.com/tag/${encodeURIComponent(query)}`;
            const subtitle = story.subtitle || story.description || "";
            const author = story.author || story.creator || (story.authors && story.authors[0]);

            return (
              <article key={story.id || idx} className="article-card">
                <div className="article-card-body">
                  <h2>
                    <a href={link} target="_blank" rel="noopener noreferrer">
                      {title}
                    </a>
                  </h2>
                  {subtitle && <p className="article-subtitle">{subtitle}</p>}
                  <div className="article-meta">
                    {author && <span className="meta-author">👤 {author}</span>}
                    {story.published_at && (
                      <span className="meta-date">
                        📅 {new Date(story.published_at).toLocaleDateString()}
                      </span>
                    )}
                    {story.claps !== undefined && (
                      <span className="meta-claps">👏 {story.claps}</span>
                    )}
                    <a
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="read-more-link"
                    >
                      Read on Medium ↗
                    </a>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {!loading && !error && stories.length > 0 && (
        <div className="pagination-controls">
          <button
            type="button"
            className="pagination-btn"
            disabled={page === 0}
            onClick={() => handlePageChange(page - 1)}
          >
            ← Previous Page
          </button>

          <span className="pagination-current">
            Page <strong>{page + 1}</strong>
          </span>

          <button
            type="button"
            className="pagination-btn"
            disabled={stories.length < 5}
            onClick={() => handlePageChange(page + 1)}
          >
            Next Page →
          </button>
        </div>
      )}
    </div>
  );
}

export default function ArticlesPage() {
  return (
    <Suspense fallback={<div className="page-loading"><div className="spinner" /><p>Loading articles...</p></div>}>
      <ArticlesContent />
    </Suspense>
  );
}
