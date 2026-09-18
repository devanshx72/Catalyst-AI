"use client";

import React, { useState } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="app-container">
      <Navbar onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <div className="layout-body">
        <Sidebar collapsed={sidebarCollapsed} />
        <main className={`main-content ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
          <div className="content-container">{children}</div>
          <footer className="footer">
            <div className="footer-content">
              <span>&copy; {new Date().getFullYear()} <strong>Catalyst AI</strong>. All rights reserved.</span>
              <span className="footer-tag">AI-Powered Career & Learning Platform</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
