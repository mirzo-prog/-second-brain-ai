export interface CourseSummary {
  id: number;
  title: string;
  description?: string;
  target_goal?: string;
  user_level: string;
  learning_mode: string;
  is_archived: boolean;
  estimated_hours: number;
  total_lessons: number;
  completed_lessons: number;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: number;
  module_id: number;
  course_id: number;
  title: string;
  description?: string;
  content_markdown?: string;
  order_index: number;
  is_completed: boolean;
  last_accessed_at?: string;
  estimated_minutes: number;
  created_at: string;
}

export interface Module {
  id: number;
  course_id: number;
  title: string;
  description?: string;
  order_index: number;
  lessons: Lesson[];
}

export interface CourseDetail extends CourseSummary {
  modules: Module[];
}

export interface LastActiveSession {
  has_active_session: boolean;
  course_id?: number;
  course_title?: string;
  lesson_id?: number;
  lesson_title?: string;
  last_accessed_at?: string;
  welcome_message: string;
}

export interface DashboardStats {
  active_courses_count: number;
  total_lessons_count: number;
  completed_lessons_count: number;
  average_progress: number;
  total_study_minutes: number;
  weak_skills_count: number;
  due_reviews_count: number;
  last_active?: LastActiveSession;
  active_courses: CourseSummary[];
  ai_recommendations: string[];
  recent_notes: Array<{
    id: number;
    title: string;
    content: string;
    tags: string;
    updated_at: string;
  }>;
}

export interface DocumentItem {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  file_size: number;
  is_indexed: boolean;
  chunks_count: number;
  attached_courses_count: number;
  created_at: string;
}

export interface SkillItem {
  id: number;
  name: string;
  description?: string;
  category: string;
  status: 'not_started' | 'learning' | 'needs_practice' | 'mastered' | 'needs_review';
  confidence_level: number;
  last_practiced_at?: string;
  next_review_at?: string;
  prerequisites: string[];
}

export interface ExerciseItem {
  id: number;
  course_id: number;
  lesson_id: number;
  title: string;
  prompt: string;
  exercise_type: 'quiz' | 'code' | 'open_question';
  initial_code?: string;
  difficulty: string;
}

export interface SettingsData {
  gemini_api_key?: string;
  gemini_api_key_configured: boolean;
  gemini_model: string;
  ollama_base_url: string;
  ollama_model: string;
  active_provider: string;
  default_learning_mode: string;
  database_size_bytes: number;
  backup_count: number;
}

const API_BASE = '/api';

async function req<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardStats: () => req<DashboardStats>('/dashboard'),

  // Sessions
  getLastActiveSession: () => req<LastActiveSession>('/sessions/last-active'),
  pingSession: (course_id: number, lesson_id?: number, seconds: number = 30) =>
    req<{ status: string; total_today_seconds: number }>('/sessions/ping', {
      method: 'POST',
      body: JSON.stringify({ course_id, lesson_id, seconds }),
    }),

  // Courses
  getCourses: (includeArchived = false) =>
    req<CourseSummary[]>(`/courses?include_archived=${includeArchived}`),
  getCourseDetail: (id: number) => req<CourseDetail>(`/courses/${id}`),
  createCourse: (data: {
    title: string;
    description?: string;
    target_goal?: string;
    user_level?: string;
    learning_mode?: string;
    estimated_hours?: number;
  }) => req<CourseDetail>('/courses', { method: 'POST', body: JSON.stringify(data) }),
  updateCourse: (id: number, data: Partial<CourseSummary>) =>
    req<CourseSummary>(`/courses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCourse: (id: number) => req<void>(`/courses/${id}`, { method: 'DELETE' }),

  // AI Generation
  generateCourseAI: (goal: string, user_level = 'beginner', learning_mode = 'free') =>
    req<CourseDetail>('/ai/generate-course', {
      method: 'POST',
      body: JSON.stringify({ goal, user_level, learning_mode }),
    }),
  generateLessonAI: (lesson_id: number) =>
    req<Lesson>('/ai/generate-lesson', {
      method: 'POST',
      body: JSON.stringify({ lesson_id }),
    }),
  testAIConnection: () => req<any>('/ai/test-connection', { method: 'POST' }),

  // Lessons
  getLesson: (id: number) => req<Lesson>(`/lessons/${id}`),
  updateLessonProgress: (id: number, is_completed: boolean) =>
    req<Lesson>(`/lessons/${id}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ is_completed }),
    }),

  // Tutor Chat
  sendChatMessage: (data: {
    course_id: number;
    lesson_id?: number;
    conversation_id?: number;
    message: string;
    learning_mode?: string;
  }) => req<{
    conversation_id: number;
    message_id: number;
    content: string;
    sources_used: string[];
    is_rag_sourced: boolean;
    learning_mode: string;
  }>('/tutor/chat', { method: 'POST', body: JSON.stringify(data) }),
  getCourseConversations: (courseId: number, lessonId?: number) =>
    req<any[]>(`/tutor/conversations/${courseId}${lessonId ? `?lesson_id=${lessonId}` : ''}`),

  // Library / Documents
  getDocuments: (courseId?: number) =>
    req<DocumentItem[]>(`/documents${courseId ? `?course_id=${courseId}` : ''}`),
  uploadDocument: async (file: File, title?: string, courseId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (courseId) formData.append('course_id', courseId.toString());
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json() as Promise<DocumentItem>;
  },
  deleteDocument: (id: number) => req<void>(`/documents/${id}`, { method: 'DELETE' }),
  attachDocument: (docId: number, courseId: number) =>
    req<any>(`/documents/${docId}/attach/${courseId}`, { method: 'POST' }),
  detachDocument: (docId: number, courseId: number) =>
    req<any>(`/documents/${docId}/attach/${courseId}`, { method: 'DELETE' }),

  // Skills
  getSkills: () => req<SkillItem[]>('/skills'),
  getSkillGraph: () => req<{ nodes: any[]; edges: any[] }>('/skills/graph'),
  updateSkillProgress: (id: number, status: string, confidence_level: number) =>
    req<SkillItem>(`/skills/${id}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ status, confidence_level }),
    }),

  // Practice & Code Sandbox
  getExercises: (courseId?: number) =>
    req<ExerciseItem[]>(`/practice/exercises${courseId ? `?course_id=${courseId}` : ''}`),
  runCode: (language: string, code: string, stdin_input = '') =>
    req<{
      success: boolean;
      stdout: string;
      stderr: string;
      exit_code: number;
      execution_time_ms: number;
    }>('/practice/run-code', {
      method: 'POST',
      body: JSON.stringify({ language, code, stdin_input }),
    }),
  submitExercise: (exercise_id: number, user_answer: string) =>
    req<{
      is_correct: boolean;
      score: number;
      feedback: string;
      next_review_in_days: number;
    }>('/practice/submit', {
      method: 'POST',
      body: JSON.stringify({ exercise_id, user_answer }),
    }),

  // Reviews
  getDueReviews: () => req<any[]>('/reviews/due'),
  gradeReview: (id: number, grade: number) =>
    req<any>(`/reviews/${id}/grade`, { method: 'POST', body: JSON.stringify({ grade }) }),

  // Statistics
  getStatistics: () => req<any>('/statistics/summary'),

  // System & Settings
  getSettings: () => req<SettingsData>('/system/settings'),
  updateSettings: (data: Partial<SettingsData>) =>
    req<SettingsData>('/system/settings', { method: 'PUT', body: JSON.stringify(data) }),
  createBackup: () => req<any>('/backup/create', { method: 'POST' }),
  listBackups: () => req<any[]>('/backup'),
  restoreBackup: (filename: string) =>
    req<any>('/backup/restore', { method: 'POST', body: JSON.stringify({ filename }) }),
};
