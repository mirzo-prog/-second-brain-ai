import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, CourseSummary } from '../api/client';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Sparkles,
  BookOpen,
  Search,
  Trash2,
  Clock,
  Layers,
  ArrowRight,
  X,
  Loader2,
} from 'lucide-react';

export const CoursesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'ai' | 'manual'>('ai');

  // Form states
  const [goal, setGoal] = useState('');
  const [level, setLevel] = useState('beginner');
  const [learningMode, setLearningMode] = useState('free');
  const [manualTitle, setManualTitle] = useState('');
  const [manualDesc, setManualDesc] = useState('');

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: () => api.getCourses(false),
  });

  const aiGenerateMutation = useMutation({
    mutationFn: () => api.generateCourseAI(goal, level, learningMode),
    onSuccess: (newCourse) => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setIsModalOpen(false);
      setGoal('');
      const firstLesson = newCourse.modules?.[0]?.lessons?.[0];
      if (firstLesson) {
        navigate(`/courses/${newCourse.id}/lessons/${firstLesson.id}`);
      } else {
        navigate(`/courses/${newCourse.id}`);
      }
    },
  });

  const manualCreateMutation = useMutation({
    mutationFn: () =>
      api.createCourse({
        title: manualTitle,
        description: manualDesc,
        target_goal: manualDesc,
        user_level: level,
        learning_mode: learningMode,
      }),
    onSuccess: (newCourse) => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setIsModalOpen(false);
      setManualTitle('');
      setManualDesc('');
      navigate(`/courses/${newCourse.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteCourse(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  const filteredCourses = courses.filter((c) =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.target_goal || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Мои курсы</h1>
          <p className="text-xs text-slate-400">Управляйте своими учебными программами и целями</p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-sm shadow-md shadow-indigo-500/20 transition-all active:scale-95 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Создать новый курс</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Поиск по названию или теме..."
          className="w-full bg-graphite-900 border border-graphite-700/80 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-indigo transition-colors"
        />
      </div>

      {/* Courses Grid */}
      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="w-8 h-8 text-brand-indigo animate-spin" />
        </div>
      ) : filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <div
              key={course.id}
              className="p-6 rounded-2xl bg-graphite-900/90 border border-graphite-700/60 hover:border-brand-indigo/50 transition-all flex flex-col justify-between group space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold tracking-wide uppercase bg-brand-indigo/15 text-indigo-300 border border-brand-indigo/30">
                    {course.user_level === 'beginner' ? 'Начинающий' : course.user_level === 'intermediate' ? 'Средний' : 'Продвинутый'}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Удалить курс «${course.title}»?`)) {
                        deleteMutation.mutate(course.id);
                      }
                    }}
                    className="text-slate-500 hover:text-red-400 transition-colors p-1"
                    title="Удалить курс"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="font-bold text-lg text-white group-hover:text-brand-indigo transition-colors line-clamp-2">
                  {course.title}
                </h3>

                <p className="text-xs text-slate-400 line-clamp-3">
                  {course.target_goal || course.description || 'Практический учебный курс.'}
                </p>
              </div>

              <div className="space-y-3 pt-4 border-t border-graphite-700/50">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" />
                    <span>{course.completed_lessons} / {course.total_lessons} уроков</span>
                  </span>
                  <span className="font-bold text-indigo-400">{course.progress_percentage}%</span>
                </div>

                <div className="w-full h-2 rounded-full bg-graphite-700 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-indigo"
                    style={{ width: `${course.progress_percentage}%` }}
                  />
                </div>

                <button
                  onClick={() => navigate(`/courses/${course.id}`)}
                  className="w-full mt-2 py-2.5 rounded-xl bg-graphite-800 hover:bg-brand-indigo text-slate-200 hover:text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all"
                >
                  <span>Перейти к курсу</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 text-center rounded-2xl bg-graphite-900/40 border border-dashed border-graphite-700 space-y-4">
          <BookOpen className="w-12 h-12 text-slate-600 mx-auto" />
          <p className="text-slate-400 text-sm">Курсы не найдены. Создайте свой первый курс!</p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-indigo hover:bg-indigo-600 text-white text-xs font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Создать курс</span>
          </button>
        </div>
      )}

      {/* Modal: Create Course */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-xl bg-graphite-900 border border-graphite-700 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-graphite-700/60 pb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-purple" />
                <span>Создание нового курса</span>
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mode Tabs */}
            <div className="flex rounded-lg bg-graphite-800 p-1 border border-graphite-700/50">
              <button
                onClick={() => setModalMode('ai')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-1.5 ${
                  modalMode === 'ai' ? 'bg-brand-indigo text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Генерация с ИИ</span>
              </button>
              <button
                onClick={() => setModalMode('manual')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  modalMode === 'manual' ? 'bg-brand-indigo text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Вручную
              </button>
            </div>

            {modalMode === 'ai' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Учебная цель или тема:
                  </label>
                  <textarea
                    rows={3}
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="Например: «Хочу изучить математику с нуля», «Создай курс биологии», «Научи меня японскому языку», «История Узбекистана», «Python с нуля»..."
                    className="w-full bg-graphite-800 border border-graphite-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Ваш начальный уровень:
                    </label>
                    <select
                      value={level}
                      onChange={(e) => setLevel(e.target.value)}
                      className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                    >
                      <option value="beginner">Начинающий (с нуля)</option>
                      <option value="intermediate">Средний (базовые знания)</option>
                      <option value="advanced">Продвинутый</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Режим обучения:
                    </label>
                    <select
                      value={learningMode}
                      onChange={(e) => setLearningMode(e.target.value)}
                      className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                    >
                      <option value="free">Свободное обучение</option>
                      <option value="my_materials_plus_ai">Мои материалы + знания ИИ</option>
                      <option value="only_my_materials">Только мои материалы</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={() => aiGenerateMutation.mutate()}
                  disabled={!goal.trim() || aiGenerateMutation.isPending}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
                >
                  {aiGenerateMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>ИИ ищет материалы и проектирует курс...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Сгенерировать курс и начать урок</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Название курса:
                  </label>
                  <input
                    type="text"
                    value={manualTitle}
                    onChange={(e) => setManualTitle(e.target.value)}
                    placeholder="Например: Архитектура Linux и системные вызовы"
                    className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Описание и цели:
                  </label>
                  <textarea
                    rows={3}
                    value={manualDesc}
                    onChange={(e) => setManualDesc(e.target.value)}
                    placeholder="Опишите, чему посвящен курс..."
                    className="w-full bg-graphite-800 border border-graphite-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
                  />
                </div>

                <button
                  onClick={() => manualCreateMutation.mutate()}
                  disabled={!manualTitle.trim() || manualCreateMutation.isPending}
                  className="w-full py-3 rounded-xl bg-brand-indigo hover:bg-indigo-600 text-white font-bold text-sm shadow-md transition-all disabled:opacity-50"
                >
                  {manualCreateMutation.isPending ? 'Создание...' : 'Создать курс'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
