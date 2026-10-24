import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, CourseDetail, Lesson } from '../api/client';
import {
  BookOpen,
  CheckCircle2,
  Circle,
  Play,
  Bot,
  Layers,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  Paperclip,
  Clock,
  Plus,
  Loader2,
} from 'lucide-react';

export const CourseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const courseId = parseInt(id || '0', 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [collapsedModules, setCollapsedModules] = useState<Record<number, boolean>>({});

  const { data: course, isLoading, error } = useQuery({
    queryKey: ['courseDetail', courseId],
    queryFn: () => api.getCourseDetail(courseId),
    enabled: courseId > 0,
  });

  const toggleLessonMutation = useMutation({
    mutationFn: ({ lessonId, isCompleted }: { lessonId: number; isCompleted: boolean }) =>
      api.updateLessonProgress(lessonId, isCompleted),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseDetail', courseId] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      queryClient.invalidateQueries({ queryKey: ['courses'] });
    },
  });

  const updateModeMutation = useMutation({
    mutationFn: (newMode: string) => api.updateCourse(courseId, { learning_mode: newMode }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseDetail', courseId] });
    },
  });

  const toggleModule = (modId: number) => {
    setCollapsedModules((prev) => ({ ...prev, [modId]: !prev[modId] }));
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[500px]">
        <Loader2 className="w-8 h-8 text-brand-indigo animate-spin" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="p-8">
        <button
          onClick={() => navigate('/courses')}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-white mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Назад к курсам</span>
        </button>
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm">
          Курс не найден или произошла ошибка загрузки.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Top Navigation */}
      <button
        onClick={() => navigate('/courses')}
        className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Ко всем курсам</span>
      </button>

      {/* Course Hero Card */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-graphite-900 via-graphite-800 to-indigo-950/40 border border-graphite-700/80 space-y-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold uppercase bg-brand-indigo/20 text-indigo-300 border border-brand-indigo/30">
                {course.user_level === 'beginner' ? 'Начинающий' : course.user_level === 'intermediate' ? 'Средний' : 'Продвинутый'}
              </span>
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span>{course.estimated_hours} ч. расчетное время</span>
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {course.title}
            </h1>

            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              {course.target_goal || course.description}
            </p>
          </div>

          <div className="flex flex-col gap-3 shrink-0">
            <button
              onClick={() => navigate(`/tutor?courseId=${course.id}`)}
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-sm shadow-md transition-all active:scale-95"
            >
              <Bot className="w-4 h-4" />
              <span>ИИ-преподаватель курса</span>
            </button>
          </div>
        </div>

        {/* Progress and Mode Controls */}
        <div className="pt-6 border-t border-graphite-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5 flex-1 max-w-md">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Прогресс курса:</span>
              <span className="font-bold text-white">{course.progress_percentage}% ({course.completed_lessons} из {course.total_lessons} уроков)</span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-graphite-700 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-indigo transition-all duration-500"
                style={{ width: `${course.progress_percentage}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Режим:</span>
            <select
              value={course.learning_mode}
              onChange={(e) => updateModeMutation.mutate(e.target.value)}
              className="bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-indigo"
            >
              <option value="free">Свободное обучение</option>
              <option value="my_materials_plus_ai">Мои материалы + знания ИИ</option>
              <option value="only_my_materials">Только мои материалы</option>
            </select>
          </div>
        </div>
      </div>

      {/* Modules and Lessons Tree */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand-indigo" />
            <span>Учебная дорожная карта ({course.modules.length} модулей)</span>
          </h2>
        </div>

        <div className="space-y-4">
          {course.modules.map((mod, modIdx) => {
            const isCollapsed = collapsedModules[mod.id];
            const completedCount = mod.lessons.filter((l) => l.is_completed).length;

            return (
              <div
                key={mod.id}
                className="rounded-2xl bg-graphite-900/90 border border-graphite-700/60 overflow-hidden shadow-sm"
              >
                {/* Module Header */}
                <div
                  onClick={() => toggleModule(mod.id)}
                  className="p-5 flex items-center justify-between cursor-pointer hover:bg-graphite-800/60 transition-colors select-none"
                >
                  <div className="flex items-center gap-3">
                    <button className="text-slate-400 hover:text-white">
                      {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                    <div>
                      <h3 className="font-bold text-base text-white">
                        Модуль {modIdx + 1}: {mod.title}
                      </h3>
                      {mod.description && <p className="text-xs text-slate-400 mt-0.5">{mod.description}</p>}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span className="px-2.5 py-1 rounded-full bg-graphite-800 border border-graphite-700">
                      {completedCount} / {mod.lessons.length} уроков
                    </span>
                  </div>
                </div>

                {/* Lesson List */}
                {!isCollapsed && (
                  <div className="border-t border-graphite-700/50 divide-y divide-graphite-700/30">
                    {mod.lessons.map((lesson, lesIdx) => (
                      <div
                        key={lesson.id}
                        className="p-4 px-6 flex items-center justify-between hover:bg-graphite-800/30 transition-colors group"
                      >
                        <div className="flex items-center gap-3.5 flex-1 min-w-0 pr-4">
                          <button
                            onClick={() =>
                              toggleLessonMutation.mutate({
                                lessonId: lesson.id,
                                isCompleted: !lesson.is_completed,
                              })
                            }
                            className="text-slate-500 hover:text-brand-emerald transition-colors shrink-0"
                            title={lesson.is_completed ? 'Отметить как не пройденный' : 'Отметить как пройденный'}
                          >
                            {lesson.is_completed ? (
                              <CheckCircle2 className="w-5 h-5 text-brand-emerald fill-brand-emerald/10" />
                            ) : (
                              <Circle className="w-5 h-5" />
                            )}
                          </button>

                          <div
                            onClick={() => navigate(`/courses/${course.id}/lessons/${lesson.id}`)}
                            className="cursor-pointer min-w-0"
                          >
                            <h4
                              className={`text-sm font-semibold truncate ${
                                lesson.is_completed ? 'line-through text-slate-500' : 'text-slate-200 group-hover:text-brand-indigo'
                              }`}
                            >
                              Урок {lesIdx + 1}: {lesson.title}
                            </h4>
                            {lesson.description && (
                              <p className="text-xs text-slate-400 truncate mt-0.5">{lesson.description}</p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-xs text-slate-500 flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" />
                            <span>{lesson.estimated_minutes} мин</span>
                          </span>

                          <button
                            onClick={() => navigate(`/courses/${course.id}/lessons/${lesson.id}`)}
                            className="px-3 py-1.5 rounded-lg bg-graphite-800 group-hover:bg-brand-indigo text-slate-300 group-hover:text-white text-xs font-semibold flex items-center gap-1.5 transition-all"
                          >
                            <Play className="w-3 h-3 fill-current" />
                            <span>Изучать</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
