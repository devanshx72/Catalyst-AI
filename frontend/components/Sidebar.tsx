"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarProps {
  collapsed?: boolean;
}

export default function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname();
  const [learningOpen, setLearningOpen] = useState(true);
  const [communityOpen, setCommunityOpen] = useState(true);

  const isActive = (path: string) => {
    if (path === "/" && pathname === "/") return true;
    if (path !== "/" && pathname?.startsWith(path)) return true;
    return false;
  };

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <nav className="sidebar-nav">
        <ul className="nav-list">
          {/* Dashboard */}
          <li className="nav-item">
            <Link
              href="/"
              className={`nav-link ${isActive("/") ? "active" : ""}`}
            >
              <span className="nav-icon">📊</span>
              {!collapsed && <span className="nav-label">Dashboard</span>}
            </Link>
          </li>

          {/* Learning Group */}
          <li className="nav-item group-item">
            <button
              type="button"
              className="nav-link group-toggle"
              onClick={() => setLearningOpen(!learningOpen)}
            >
              <span className="nav-icon">📚</span>
              {!collapsed && (
                <>
                  <span className="nav-label">Learning</span>
                  <span className={`chevron ${learningOpen ? "open" : ""}`}>▾</span>
                </>
              )}
            </button>
            {!collapsed && learningOpen && (
              <ul className="sub-nav-list">
                <li>
                  <Link
                    href="/resources"
                    className={`sub-link ${isActive("/resources") ? "active" : ""}`}
                  >
                    Resources
                  </Link>
                </li>
                <li>
                  <Link
                    href="/articles"
                    className={`sub-link ${isActive("/articles") ? "active" : ""}`}
                  >
                    Tech News
                  </Link>
                </li>
              </ul>
            )}
          </li>

          {/* Community Group */}
          <li className="nav-item group-item">
            <button
              type="button"
              className="nav-link group-toggle"
              onClick={() => setCommunityOpen(!communityOpen)}
            >
              <span className="nav-icon">👥</span>
              {!collapsed && (
                <>
                  <span className="nav-label">Community</span>
                  <span className={`chevron ${communityOpen ? "open" : ""}`}>▾</span>
                </>
              )}
            </button>
            {!collapsed && communityOpen && (
              <ul className="sub-nav-list">
                <li>
                  <Link
                    href="/profile"
                    className={`sub-link ${isActive("/profile") ? "active" : ""}`}
                  >
                    Student Profile
                  </Link>
                </li>
              </ul>
            )}
          </li>

          {/* Roadmap */}
          <li className="nav-item">
            <Link
              href="/roadmap"
              className={`nav-link ${isActive("/roadmap") ? "active" : ""}`}
            >
              <span className="nav-icon">🗺️</span>
              {!collapsed && <span className="nav-label">Roadmap</span>}
            </Link>
          </li>

          {/* Leo Coach */}
          <li className="nav-item">
            <Link
              href="/coach"
              className={`nav-link ${isActive("/coach") ? "active" : ""}`}
            >
              <span className="nav-icon">🤖</span>
              {!collapsed && <span className="nav-label">Leo Coach</span>}
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
