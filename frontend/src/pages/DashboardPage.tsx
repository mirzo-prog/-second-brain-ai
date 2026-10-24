import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  BookOpen,
  CheckCircle2,
  Clock,
  TrendingUp,
  AlertTriangle,
  Calendar,
  Sparkles,
  ArrowRight,
  FileText,
  Plus,
  Loader2,
  Search,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [quickGoal, setQuickGoal] = useState('');

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 15000,
  });

  const quickCreateMutation = useMutation({
    mutationFn: () => api.generateCourseAI(quickGoal.trim(), 'beginner', 'free'),
    onSuccess: (newCourse) => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      const firstLesson = newCourse.modules?.[0]?.lessons?.[0];
      if (firstLesson) {
        navigate(`/courses/${newCourse.id}/lessons/${firstLesson.id}`);
      } else {
        navigate(`/courses/${newCourse.id}`);
      }
    },
  });

  const handleQuickCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickGoal.trim()) return;
    quickCreateMutation.mutate();
  };

  const handleResume = () => {
    if (stats?.last_active?.has_active_session && stats.last_active.lesson_id) {
      navigate(`/courses/${stats.last_active.course_id}/lessons/${stats.last_active.lesson_id}`);
    } else if (stats?.last_active?.course_id) {
      navigate(`/courses/${stats.last_active.course_id}`);
    } else {
      navigate('/courses');
    }
  };

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins} мин`;
    return `${hours} ч ${mins} мин`;
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-brand-indigo/30 border-t-brand-indigo rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Загрузка данных Second Brain AI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-sm">
          Ошибка загрузки данных: {(error as Error).message}
        </div>
      </div>
    );
  }

  const lastActive = stats?.last_active;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Hero: Resume Session Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-graphite-900 via-graphite-800 to-indigo-950/50 border border-brand-indigo/30 p-8 shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-brand-indigo/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-indigo/20 border border-brand-indigo/40 text-xs text-indigo-300 font-medium">
              <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
              <span>Постоянная память & Контекст обучения</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {lastActive?.welcome_message || 'Готовы продолжить обучение?'}
            </h1>
            <p className="text-sm text-slate-400">
              {lastActive?.has_active_session
                ? `Курс: ${lastActive.course_title} • Урок: ${lastActive.lesson_title}`
                : 'Создайте курс или выберите готовую учебную программу, чтобы начать.'}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={handleResume}
              className="flex items-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-brand-blue via-brand-indigo to-brand-purple hover:from-blue-600 hover:to-purple-600 text-white font-bold text-base shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 active:scale-95"
            >
              <Play className="w-5 h-5 fill-current" />
              <span>Продолжить обучение</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Topic Course & Materials Generator */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-graphite-900/90 to-graphite-800/80 border border-brand-indigo/30 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-blue/20 flex items-center justify-center text-brand-blue">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Создать курс по любой теме с материалами</h2>
              <p className="text-xs text-slate-400">Введите тему — ИИ найдёт материалы, составит программу и сразу начнёт первый урок</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleQuickCreate} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={quickGoal}
              onChange={(e) => setQuickGoal(e.target.value)}
              placeholder="Например: Python с нуля, История Рима, Веб-разработка, Английский, C++..."
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-graphite-950/80 border border-graphite-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-brand-indigo transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={!quickGoal.trim() || quickCreateMutation.isPending}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-brand-blue via-brand-indigo to-brand-purple hover:from-blue-600 hover:to-purple-600 text-white font-semibold text-sm shadow-md shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0"
          >
            {quickCreateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Создаём курс и ищем материалы...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Создать и начать урок</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-blue/15 border border-brand-blue/30 flex items-center justify-center text-brand-blue">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Активные курсы</p>
            <h3 className="text-2xl font-bold text-white">{stats?.active_courses_count || 0}</h3>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-emerald/15 border border-brand-emerald/30 flex items-center justify-center text-brand-emerald">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Пройденные уроки</p>
            <h3 className="text-2xl font-bold text-white">
              {stats?.completed_lessons_count || 0}{' '}
              <span className="text-sm font-normal text-slate-400">/ {stats?.total_lessons_count || 0}</span>
            </h3>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-purple/15 border border-brand-purple/30 flex items-center justify-center text-brand-purple">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Время обучения</p>
            <h3 className="text-2xl font-bold text-white">
              {formatStudyTime(stats?.total_study_minutes || 0)}
            </h3>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-indigo/15 border border-brand-indigo/30 flex items-center justify-center text-brand-indigo">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Средний прогресс</p>
            <h3 className="text-2xl font-bold text-white">{stats?.average_progress || 0}%</h3>
          </div>
        </div>
      </div>

      {/* Two Column Grid: Active Courses & Learning Assistant Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Active Courses (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Текущие курсы</h2>
            <button
              onClick={() => navigate('/courses')}
              className="text-xs text-brand-indigo hover:text-indigo-400 font-medium flex items-center gap-1"
            >
              <span>Все курсы</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {stats?.active_courses && stats.active_courses.length > 0 ? (
              stats.active_courses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => navigate(`/courses/${course.id}`)}
                  className="p-5 rounded-xl bg-graphite-900/80 hover:bg-graphite-800/90 border border-graphite-700/60 transition-all cursor-pointer group space-y-3"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="font-bold text-white group-hover:text-brand-indigo transition-colors">
                        {course.title}
                      </h4>
                      <p className="text-xs text-slate-400 line-clamp-1">{course.target_goal || course.description}</p>
                    </div>
                    <span className="text-xs font-bold text-indigo-400 shrink-0">
                      {course.progress_percentage}%
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-graphite-700/80 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-indigo transition-all duration-500"
                      style={{ width: `${course.progress_percentage}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      {course.completed_lessons} из {course.total_lessons} уроков
                    </span>
                    <span className="capitalize">Уровень: {course.user_level}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 rounded-xl bg-graphite-900/40 border border-dashed border-graphite-700/70 text-center space-y-3">
                <p className="text-sm text-slate-400">У вас пока нет активных курсов.</p>
                <button
                  onClick={() => navigate('/courses')}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-indigo hover:bg-indigo-600 text-white text-xs font-semibold"
                >
                  <Plus className="w-4 h-4" />
                  <span>Создать первый курс с ИИ</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right: AI Tutor & Review Alerts */}
        <div className="space-y-6">
          {/* AI Recommendations */}
          <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-purple" />
              <span>Рекомендации ИИ</span>
            </h3>
            <ul className="space-y-2.5">
              {stats?.ai_recommendations?.map((rec, i) => (
                <li key={i} className="text-xs text-slate-300 flex items-start gap-2 bg-graphite-800/50 p-2.5 rounded-lg border border-graphite-700/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-indigo mt-1.5 shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Weak Skills & Scheduled Reviews Alerts */}
          <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Calendar className="w-4 h-4 text-brand-amber" />
                <span>Запланировано</span>
              </h3>
            </div>

            <div className="space-y-3">
              <div
                onClick={() => navigate('/study-plan')}
                className="flex items-center justify-between p-3 rounded-lg bg-graphite-800/60 hover:bg-graphite-800 border border-graphite-700/50 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-2.5 text-xs text-slate-300">
                  <Clock className="w-4 h-4 text-brand-blue" />
                  <span>Повторений на сегодня:</span>
                </div>
                <span className="font-bold text-sm text-white px-2 py-0.5 rounded bg-brand-blue/20 text-blue-300">
                  {stats?.due_reviews_count || 0}
                </span>
              </div>

              <div
                onClick={() => navigate('/skills')}
                className="flex items-center justify-between p-3 rounded-lg bg-graphite-800/60 hover:bg-graphite-800 border border-graphite-700/50 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-2.5 text-xs text-slate-300">
                  <AlertTriangle className="w-4 h-4 text-brand-amber" />
                  <span>Слабых навыков:</span>
                </div>
                <span className="font-bold text-sm text-white px-2 py-0.5 rounded bg-brand-amber/20 text-amber-300">
                  {stats?.weak_skills_count || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Recent Notes */}
          {stats?.recent_notes && stats.recent_notes.length > 0 && (
            <div className="p-5 rounded-xl bg-graphite-900/90 border border-graphite-700/60 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-emerald" />
                <span>Последние конспекты</span>
              </h3>
              <div className="space-y-2">
                {stats.recent_notes.slice(0, 3).map((note) => (
                  <div key={note.id} className="p-2.5 rounded-lg bg-graphite-800/40 border border-graphite-700/30">
                    <h5 className="text-xs font-semibold text-white truncate">{note.title}</h5>
                    <p className="text-[11px] text-slate-400 line-clamp-1">{note.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
