/**
 * Centralized Typed API Client for Catalyst AI.
 *
 * Architecture:
 * - All calls route through Next.js rewrites to /api/v1/*, keeping frontend and backend
 *   same-origin in both dev and production (no CORS issues).
 * - Credentials ('include') are supplied to send the HTTP-only signed session cookie.
 * - Supports JSON REST requests and Server-Sent Events (SSE) streaming for the AI Tutor.
 */

import type {
  ArticlesResponse,
  ClearHistoryResponse,
  CoachChatResponse,
  CoachClearHistoryResponse,
  CoachMessagesResponse,
  HomeResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MentorshipResponse,
  NotificationItem,
  PhasePlanResponse,
  PlanGenerateResponse,
  ProfileResponse,
  ProfileUpdateRequest,
  RegisterRequest,
  RegisterResponse,
  ResourceResponse,
  RoadmapResponse,
  TaskCompleteRequest,
  TaskCompleteResponse,
  TutorContextResponse,
} from "@/types";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Ensure session cookie is transmitted
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let responseData: any = null;
    try {
      responseData = await response.json();
      if (responseData && typeof responseData === "object") {
        if (typeof responseData.detail === "string") {
          errorDetail = responseData.detail;
        } else if (Array.isArray(responseData.detail)) {
          errorDetail = responseData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
        } else if (typeof responseData.message === "string") {
          errorDetail = responseData.message;
        }
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiError(response.status, errorDetail, responseData);
  }

  // Handle empty responses
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ── Auth Service ─────────────────────────────────────────────────────────────

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>("/api/v1/auth/logout", {
    method: "POST",
  });
}

// ── Profile Service ──────────────────────────────────────────────────────────

export async function getProfile(): Promise<ProfileResponse> {
  return request<ProfileResponse>("/api/v1/profile", {
    method: "GET",
  });
}

export async function updateProfile(data: ProfileUpdateRequest): Promise<ProfileResponse> {
  return request<ProfileResponse>("/api/v1/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ── Roadmap Service ──────────────────────────────────────────────────────────

export async function getRoadmap(): Promise<RoadmapResponse> {
  return request<RoadmapResponse>("/api/v1/roadmap", {
    method: "GET",
  });
}

export async function generatePhasePlan(phaseId: number): Promise<PlanGenerateResponse> {
  return request<PlanGenerateResponse>(`/api/v1/roadmap/phases/${phaseId}/plan`, {
    method: "POST",
  });
}

export async function getPhasePlan(phaseId: number): Promise<PhasePlanResponse> {
  return request<PhasePlanResponse>(`/api/v1/roadmap/phases/${phaseId}/plan`, {
    method: "GET",
  });
}

export async function completeTask(data: TaskCompleteRequest): Promise<TaskCompleteResponse> {
  return request<TaskCompleteResponse>("/api/v1/roadmap/tasks/complete", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── AI Tutor Service ─────────────────────────────────────────────────────────

export async function getTutorContext(
  phaseId: number,
  moduleId: number,
): Promise<TutorContextResponse> {
  return request<TutorContextResponse>(`/api/v1/tutor/${phaseId}/${moduleId}`, {
    method: "GET",
  });
}

export async function clearTutorHistory(
  phaseId: number,
  moduleId: number,
): Promise<ClearHistoryResponse> {
  return request<ClearHistoryResponse>(`/api/v1/tutor/${phaseId}/${moduleId}/history`, {
    method: "DELETE",
  });
}

export async function getTutorResources(
  topic: string,
  type: string = "all",
): Promise<ResourceResponse> {
  const params = new URLSearchParams({ topic, type });
  return request<ResourceResponse>(`/api/v1/tutor/resources?${params.toString()}`, {
    method: "GET",
  });
}

/**
 * Stream AI Tutor response via Server-Sent Events (SSE).
 *
 * @param phaseId Roadmap phase ID
 * @param moduleId Module (week) index
 * @param message Student's prompt
 * @param onToken Callback invoked with each incoming text token
 * @param onDone Callback invoked when stream completes
 * @param onError Callback invoked on error
 */
export async function streamTutorChat(
  phaseId: number,
  moduleId: number,
  message: string,
  onToken: (token: string) => void,
  onDone?: () => void,
  onError?: (error: any) => void,
): Promise<void> {
  try {
    const response = await fetch(`/api/v1/tutor/${phaseId}/${moduleId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      let errorDetail = `Streaming failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errorDetail;
      } catch {
        // Fallback
      }
      throw new ApiError(response.status, errorDetail);
    }

    if (!response.body) {
      throw new Error("Response body is empty");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        const dataContent = trimmed.replace(/^data:\s*/, "");
        if (dataContent === "[DONE]") {
          if (onDone) onDone();
          return;
        }

        try {
          const parsed = JSON.parse(dataContent);
          if (parsed.token) {
            onToken(parsed.token);
          } else if (parsed.error) {
            throw new Error(parsed.error);
          }
        } catch (e) {
          // If not valid JSON, treat as raw text token
          if (dataContent !== "[DONE]") {
            onToken(dataContent);
          }
        }
      }
    }

    if (onDone) onDone();
  } catch (error) {
    if (onError) {
      onError(error);
    } else {
      throw error;
    }
  }
}

// ── Career Coach (Leo) Service ───────────────────────────────────────────────

export async function getCoachMessages(): Promise<CoachMessagesResponse> {
  return request<CoachMessagesResponse>("/api/v1/coach/messages", {
    method: "GET",
  });
}

export async function chatWithCoach(message: string): Promise<CoachChatResponse> {
  return request<CoachChatResponse>("/api/v1/coach/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function clearCoachHistory(): Promise<CoachClearHistoryResponse> {
  return request<CoachClearHistoryResponse>("/api/v1/coach/history", {
    method: "DELETE",
  });
}

// ── Home / Articles / Notifications / Mentorship ─────────────────────────────

export async function getHome(): Promise<HomeResponse> {
  return request<HomeResponse>("/api/v1/home", {
    method: "GET",
  });
}

export async function getArticles(q: string = "technology", page: number = 0): Promise<ArticlesResponse> {
  const params = new URLSearchParams({ q, page: page.toString() });
  return request<ArticlesResponse>(`/api/v1/articles?${params.toString()}`, {
    method: "GET",
  });
}

export async function getNotifications(): Promise<NotificationItem[]> {
  return request<NotificationItem[]>("/api/v1/notifications", {
    method: "GET",
  });
}

export async function getMentorshipStatus(): Promise<MentorshipResponse> {
  return request<MentorshipResponse>("/api/v1/mentorship", {
    method: "GET",
  });
}

// Export default namespace bundle
const api = {
  // Auth
  register,
  login,
  logout,
  // Profile
  getProfile,
  updateProfile,
  // Roadmap
  getRoadmap,
  generatePhasePlan,
  getPhasePlan,
  completeTask,
  // Tutor
  getTutorContext,
  clearTutorHistory,
  getTutorResources,
  streamTutorChat,
  // Coach
  getCoachMessages,
  chatWithCoach,
  clearCoachHistory,
  // Home / Articles / Notifications / Mentorship
  getHome,
  getArticles,
  getNotifications,
  getMentorshipStatus,
};

export default api;
