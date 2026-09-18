/**
 * TypeScript definitions mirroring backend Pydantic schemas (backend/app/schemas/).
 */

// ── Auth Schemas (backend/app/schemas/auth.py) ────────────────────────────────

export interface RegisterRequest {
  username: string;
  name: string;
  email: string;
  phone: string;
  dob: string;
  password: string;
  confirm_password: string;
  joining_date?: string;
  career_goal?: string;
  entrepreneurship_interest?: string;
  interested_industries?: string;
  dream_company?: string;
  company_preference?: string;
  preferred_company?: string;
  personal_statement?: string;
  github_profile?: string;
  linkedin_profile?: string;
}

export interface RegisterResponse {
  message: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  user_id: string;
  name: string;
}

export interface LogoutResponse {
  message: string;
}

// ── Profile Schemas (backend/app/schemas/profile.py) ──────────────────────────

export interface ProfileResponse {
  user_id: string;
  name: string;
  email: string;
  phone?: string | null;
  dob?: string | null;
  gender?: string | null;
  joining_date?: string | null;
  enddate?: string | null;
  career_goal?: string | null;
  learning_duration?: string | null;
  learning_duration_unit?: string | null;
  dream_company?: string | null;
  company_preference?: string | null;
  preferred_company?: string | null;
  entrepreneurship_interest?: string | null;
  key_interests?: string[] | null;
  interested_industries?: string | null;
  personal_statement?: string | null;
  github_profile?: string | null;
  linkedin_profile?: string | null;
  linkedin_data?: Record<string, any> | null;
  road_map?: any | null;
  active_modules?: any[] | null;
}

export interface ProfileUpdateRequest {
  name?: string;
  phone?: string;
  dob?: string;
  gender?: string;
  joining_date?: string;
  startdate?: string;
  enddate?: string;
  career_goal?: string;
  learning_duration?: string;
  learning_duration_unit?: string;
  dream_company?: string;
  company_preference?: string;
  preferred_company?: string;
  entrepreneurship_interest?: string;
  key_interests?: string[];
  interested_industries?: string;
  personal_statement?: string;
  github_profile?: string;
  githubProfile?: string;
  linkedin_profile?: string;
  linkedinProfile?: string;
}

// ── Roadmap Schemas (backend/app/schemas/roadmap.py) ──────────────────────────

export interface DailyTask {
  day: number;
  tasks: string[];
  resources?: string[];
  duration_hours?: number;
  completed?: boolean;
}

export interface WeeklyScheduleItem {
  week: number;
  learning_objectives: string[];
  daily_tasks: DailyTask[];
  assessment?: string | null;
}

export interface LearningPlan {
  weekly_schedule: WeeklyScheduleItem[];
}

export interface RoadmapResponse {
  has_career_goal: boolean;
  has_roadmap: boolean;
  career_goal?: string | null;
  roadmap_data?: Record<string, any> | null;
}

export interface PhasePlanResponse {
  phase_id: number;
  phase_name: string;
  skills: string[];
  learning_plan: LearningPlan;
}

export interface PlanGenerateResponse {
  status: string;
  message: string;
  phase_id: number;
  learning_plan: LearningPlan;
}

export interface TaskCompleteRequest {
  phase_id: number;
  week_index: number;
  day_index: number;
  completed?: boolean;
}

export interface TaskCompleteResponse {
  status: string;
  message: string;
  phase_id: number;
  week_index: number;
  day_index: number;
  completed: boolean;
}

// ── Tutor Schemas (backend/app/schemas/tutor.py) ──────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant" | string;
  content: string;
  timestamp?: string | null;
}

export interface TutorContextResponse {
  user_id: string;
  phase_id: number;
  module_id: number;
  phase_name: string;
  topic: string;
  objectives: string[];
  skills: string[];
  resources: Record<string, any>;
  chat_history: ChatMessage[];
}

export interface TutorChatRequest {
  message: string;
}

export interface ClearHistoryResponse {
  status: string;
  message: string;
}

export interface ResourceResponse {
  status: string;
  resources: Record<string, any>;
}

// ── Career Coach Schemas (backend/app/schemas/coach.py) ───────────────────────

export interface CoachMessage {
  prompt: string;
  response: string;
  raw_response: string;
  time?: string | null;
}

export interface CoachMessagesResponse {
  messages: CoachMessage[];
  conversation_id?: string | null;
}

export interface CoachChatRequest {
  message: string;
}

export interface CoachChatResponse {
  prompt: string;
  response: string;
  raw_response: string;
  messages: CoachMessage[];
}

export interface CoachClearHistoryResponse {
  status: string;
  message: string;
}

// ── Home / Articles / Notifications Schemas (backend/app/schemas/home.py) ────

export interface HomeResponse {
  categories: string[];
  companies: Record<string, any>[];
  stories: Record<string, any>[];
}

export interface ArticlesResponse {
  query: string;
  page: number;
  categories: string[];
  stories: Record<string, any>[];
}

export interface NotificationItem {
  id?: string | null;
  _id?: string | null;
  user_id: string;
  read: boolean;
  created_at?: string | null;
  title?: string | null;
  message?: string | null;
  [key: string]: any;
}

export interface MentorshipResponse {
  status: string;
  message: string;
}
