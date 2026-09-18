"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import api from "@/lib/api";
import type { NotificationItem } from "@/types";

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export default function Navbar({ onToggleSidebar }: NavbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const { user, isAuthenticated, logout } = useAuth();

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const items = await api.getNotifications();
      setNotifications(items || []);
    } catch (err) {
      // Degrades cleanly if notification service is empty
      console.debug("Notifications fetch:", err);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "U";
  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <header className="navbar">
      <div className="navbar-left">
        <button
          type="button"
          className="sidebar-toggle-btn"
          aria-label="Toggle sidebar"
          onClick={onToggleSidebar}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <Link href="/dashboard" className="navbar-brand">
          <span className="brand-badge">⚡</span>
          <span className="brand-title">Catalyst AI</span>
        </Link>
      </div>

      <div className="navbar-right">
        {/* Notification Bell Dropdown */}
        <div className="dropdown-container">
          <button
            type="button"
            className="nav-icon-btn"
            aria-label="Notifications"
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfileMenu(false);
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
          </button>

          {showNotifications && (
            <div className="dropdown-panel notification-dropdown">
              <div className="dropdown-header">
                <span className="dropdown-title">Notifications ({unreadCount})</span>
                <button
                  type="button"
                  className="text-btn"
                  onClick={() => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))}
                >
                  Mark all read
                </button>
              </div>

              <div className="notification-list-container">
                {notifications.length === 0 ? (
                  <div className="notification-empty">
                    <p>No new notifications</p>
                  </div>
                ) : (
                  <div className="notification-items">
                    {notifications.map((n, idx) => (
                      <div key={n.id || n._id || idx} className={`notification-item ${!n.read ? "unread" : ""}`}>
                        <div className="notification-bullet">🔔</div>
                        <div className="notification-content">
                          <p className="notification-msg">{n.title || n.message || "Notification"}</p>
                          {n.created_at && (
                            <span className="notification-time">
                              {new Date(n.created_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar Dropdown */}
        <div className="dropdown-container">
          <button
            type="button"
            className="profile-btn"
            aria-label="User Profile"
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
            }}
          >
            <div className="avatar-placeholder">{userInitial}</div>
          </button>

          {showProfileMenu && (
            <div className="dropdown-panel profile-dropdown">
              <div className="profile-header">
                <strong>{user?.name || "Student Account"}</strong>
                <span className="user-subtitle">{user?.email || user?.user_id || "Active Session"}</span>
              </div>
              <ul className="dropdown-list">
                <li>
                  <Link
                    href="/profile"
                    className="dropdown-item"
                    onClick={() => setShowProfileMenu(false)}
                  >
                    My Profile
                  </Link>
                </li>
                <li>
                  <Link
                    href="/dashboard"
                    className="dropdown-item"
                    onClick={() => setShowProfileMenu(false)}
                  >
                    Dashboard
                  </Link>
                </li>
                <li className="dropdown-divider" />
                <li>
                  <button
                    type="button"
                    className="dropdown-item danger"
                    onClick={() => {
                      setShowProfileMenu(false);
                      logout();
                    }}
                  >
                    Logout
                  </button>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
