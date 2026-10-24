import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  Clock,
  Sparkles,
  Bot,
  FileText,
  Save,
  Loader2,
  ChevronRight,
  Airplay,
  Maximize2,
} from 'lucide-react';
import { PresentationViewer } from '../components/education/PresentationViewer';
import { InteractiveQuiz } from '../components/education/InteractiveQuiz';
import { FocusModeModal } from '../components/education/FocusModeModal';

export const LessonViewPage: React.FC = () => {
  const { courseId: cId, lessonId: lId } = useParams<{ courseId: string; lessonId: string }>();
  const courseId = parseInt(cId || '0', 10);
  const lessonId = parseInt(lId || '0', 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [studySeconds, setStudySeconds] = useState(0);
  const [noteContent, setNoteContent] = useState('');
  const [noteSaved, setNoteSaved] = useState(false);
  const [isPresentationOpen, setIsPresentationOpen] = useState(false);
  const [isFocusModeOpen, setIsFocusModeOpen] = useState(false);

  const { data: lesson, isLoading, error } = useQuery({
    queryKey: ['lesson', lessonId],
    queryFn: () => api.getLesson(lessonId),
    enabled: lessonId > 0,
  });

  const { data: course } = useQuery({
    queryKey: ['courseDetail', courseId],
    queryFn: () => api.getCourseDetail(courseId),
    enabled: courseId > 0,
  });

  const allLessons = course?.modules?.flatMap((m) => m.lessons) || [];
  const currentLessonIndex = allLessons.findIndex((l) => l.id === lessonId);
  const nextLesson =
    currentLessonIndex >= 0 && currentLessonIndex < allLessons.length - 1
      ? allLessons[currentLessonIndex + 1]
      : null;

  // Live real study timer: records seconds and pings backend every 30 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setStudySeconds((prev) => prev + 1);
    }, 1000);

    const pingTimer = setInterval(() => {
      if (courseId > 0 && lessonId > 0) {
        api.pingSession(courseId, lessonId, 30).catch(() => {});
      }
    }, 30000);

    return () => {
      clearInterval(timer);
      clearInterval(pingTimer);
    };
  }, [courseId, lessonId]);

  const toggleCompleteMutation = useMutation({
    mutationFn: (completed: boolean) => api.updateLessonProgress(lessonId, completed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lesson', lessonId] });
      queryClient.invalidateQueries({ queryKey: ['courseDetail', courseId] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  const aiGenerateMutation = useMutation({
    mutationFn: () => api.generateLessonAI(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lesson', lessonId] });
    },
  });

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[500px]">
        <Loader2 className="w-8 h-8 text-brand-indigo animate-spin" />
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="p-8">
        <button
          onClick={() => navigate(`/courses/${courseId}`)}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-white mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Назад к курсу</span>
        </button>
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm">
          Урок не найден.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Top Bar Navigation & Active Timer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-graphite-700/60 pb-4">
        <button
          onClick={() => navigate(`/courses/${courseId}`)}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>К курсу: {course?.title || 'Курс'}</span>
        </button>

        <div className="flex items-center gap-4">
          {/* Active study time tracker */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-graphite-900 border border-graphite-700 text-xs text-slate-300">
            <Clock className="w-3.5 h-3.5 text-brand-purple animate-pulse" />
            <span>Время занятия:</span>
            <span className="font-mono font-bold text-white">{formatTimer(studySeconds)}</span>
          </div>

          <button
            onClick={() => toggleCompleteMutation.mutate(!lesson.is_completed)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-sm ${
              lesson.is_completed
                ? 'bg-brand-emerald/20 text-brand-emerald border border-brand-emerald/40 hover:bg-brand-emerald/30'
                : 'bg-graphite-800 text-slate-300 hover:bg-brand-emerald hover:text-white border border-graphite-700'
            }`}
          >
            {lesson.is_completed ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Урок пройден</span>
              </>
            ) : (
              <>
                <Circle className="w-4 h-4" />
                <span>Отметить как пройденный</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Lesson Header */}
      <div className="space-y-3">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">{lesson.title}</h1>
        {lesson.description && <p className="text-sm text-slate-400">{lesson.description}</p>}

        <div className="flex flex-wrap items-center gap-3 pt-2">
          {/* Open Presentation */}
          <button
            onClick={() => setIsPresentationOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600/90 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition-all"
            title="Открыть интерактивную презентацию слайдов к уроку"
          >
            <Airplay className="w-3.5 h-3.5" />
            <span>Открыть презентацию</span>
          </button>

          {/* Focus Mode */}
          <button
            onClick={() => setIsFocusModeOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-purple-600/90 hover:bg-purple-500 text-white text-xs font-semibold shadow transition-all"
            title="Перейти в чистый режим фокуса с таймером Помодоро"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Режим фокуса</span>
          </button>

          <button
            onClick={() => navigate(`/tutor?courseId=${courseId}&lessonId=${lessonId}`)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white text-xs font-semibold shadow transition-all"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Задать вопрос ИИ-преподавателю</span>
          </button>

          <button
            onClick={() => aiGenerateMutation.mutate()}
            disabled={aiGenerateMutation.isPending}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-graphite-800 hover:bg-graphite-700 border border-graphite-700 text-xs font-semibold text-slate-300 transition-all disabled:opacity-50"
          >
            {aiGenerateMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-purple" />
                <span>Генерация урока...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
                <span>Обновить / углубить урок с ИИ</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Lesson Markdown Content */}
      <div className="p-8 rounded-2xl bg-graphite-900/90 border border-graphite-700/70 shadow-xl space-y-6">
        <div className="prose prose-invert max-w-none space-y-4 text-slate-200 leading-relaxed text-sm">
          {lesson.content_markdown?.split('\n\n').map((block, idx) => {
            if (block.startsWith('# ')) {
              return <h1 key={idx} className="text-2xl font-bold text-white border-b border-graphite-700 pb-2">{block.replace('# ', '')}</h1>;
            }
            if (block.startsWith('## ')) {
              return <h2 key={idx} className="text-xl font-bold text-indigo-300 pt-3">{block.replace('## ', '')}</h2>;
            }
            if (block.startsWith('### ')) {
              return <h3 key={idx} className="text-base font-semibold text-slate-200">{block.replace('### ', '')}</h3>;
            }
            if (block.startsWith('> [!NOTE]')) {
              return (
                <div key={idx} className="p-4 rounded-xl bg-brand-blue/10 border-l-4 border-brand-blue text-xs text-blue-200 space-y-1">
                  <span className="font-bold uppercase tracking-wider block">Дополнение ИИ:</span>
                  <p>{block.replace('> [!NOTE]', '').trim()}</p>
                </div>
              );
            }
            if (block.startsWith('> ')) {
              return (
                <blockquote key={idx} className="p-3 rounded-lg bg-graphite-800/60 border-l-4 border-brand-indigo text-slate-300 italic text-xs">
                  {block.replace('> ', '')}
                </blockquote>
              );
            }
            if (block.startsWith('```')) {
              const codeLines = block.split('\n');
              const code = codeLines.slice(1, -1).join('\n');
              return (
                <pre key={idx} className="p-4 rounded-xl bg-graphite-950 border border-graphite-700/80 font-mono text-xs text-emerald-300 overflow-x-auto shadow-inner">
                  <code>{code}</code>
                </pre>
              );
            }
            return <p key={idx} className="text-slate-300">{block}</p>;
          })}
        </div>
      </div>

      {/* Interactive Quiz Component */}
      <InteractiveQuiz
        lessonTitle={lesson.title}
        quizJson={lesson.quiz_json}
        onComplete={(score, total) => {
          if (score / total >= 0.6) {
            toggleCompleteMutation.mutate(true);
          }
        }}
      />

      {/* Interactive AI Tutor Assistance Bar */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-graphite-900 to-indigo-950/40 border border-brand-indigo/30 space-y-3 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-brand-indigo" />
            <h3 className="text-sm font-bold text-white">Интерактивный ИИ-преподаватель</h3>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Gemini Tutor Context Engine</span>
        </div>

        <p className="text-xs text-slate-300">
          ИИ-преподаватель знает контекст этого урока и готов помочь в любую секунду:
        </p>

        <div className="flex flex-wrap items-center gap-2.5 pt-1">
          <button
            onClick={() =>
              navigate(
                `/tutor?courseId=${courseId}&lessonId=${lessonId}&prompt=${encodeURIComponent(
                  `Объясни тему урока «${lesson.title}» проще и понятнее, с жизненной аналогией.`
                )}`
              )
            }
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-graphite-800 hover:bg-brand-indigo border border-graphite-700/80 hover:border-brand-indigo text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-sm"
          >
            <span>💡 Объясни проще</span>
          </button>

          <button
            onClick={() =>
              navigate(
                `/tutor?courseId=${courseId}&lessonId=${lessonId}&prompt=${encodeURIComponent(
                  `Приведи подробный практический пример по теме «${lesson.title}».`
                )}`
              )
            }
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-graphite-800 hover:bg-brand-indigo border border-graphite-700/80 hover:border-brand-indigo text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-sm"
          >
            <span>💻 Покажи пример</span>
          </button>

          <button
            onClick={() =>
              navigate(
                `/tutor?courseId=${courseId}&lessonId=${lessonId}&prompt=${encodeURIComponent(
                  `Дай мне проверочное практическое задание по уроку «${lesson.title}».`
                )}`
              )
            }
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-graphite-800 hover:bg-brand-indigo border border-graphite-700/80 hover:border-brand-indigo text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-sm"
          >
            <span>📝 Дай задание</span>
          </button>

          <button
            onClick={() =>
              navigate(
                `/tutor?courseId=${courseId}&lessonId=${lessonId}&prompt=${encodeURIComponent(
                  `Проверь мои знания по уроку «${lesson.title}»: задай мне 3 вопроса по очереди.`
                )}`
              )
            }
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-graphite-800 hover:bg-brand-indigo border border-graphite-700/80 hover:border-brand-indigo text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-sm"
          >
            <span>🎯 Проверь мои знания</span>
          </button>

          {nextLesson && (
            <button
              onClick={() => {
                toggleCompleteMutation.mutate(true);
                navigate(`/courses/${courseId}/lessons/${nextLesson.id}`);
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition-all ml-auto"
            >
              <span>Продолжить урок</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Quick Notes Panel */}
      <div className="p-6 rounded-2xl bg-graphite-900/70 border border-graphite-700/60 space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-emerald" />
          <span>Быстрая заметка по уроку</span>
        </h3>
        <textarea
          rows={3}
          value={noteContent}
          onChange={(e) => {
            setNoteContent(e.target.value);
            setNoteSaved(false);
          }}
          placeholder="Запишите ключевые мысли или выводы из этого урока..."
          className="w-full bg-graphite-800 border border-graphite-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-brand-emerald">{noteSaved && '✓ Заметка сохранена в постоянную память'}</span>
          <button
            onClick={async () => {
              if (noteContent.trim()) {
                await fetch('/api/notes', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    course_id: courseId,
                    lesson_id: lessonId,
                    title: `Заметка: ${lesson.title}`,
                    content: noteContent,
                  }),
                });
                setNoteSaved(true);
              }
            }}
            disabled={!noteContent.trim()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-graphite-800 hover:bg-brand-indigo text-slate-200 hover:text-white text-xs font-semibold disabled:opacity-50 transition-all"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Сохранить заметку</span>
          </button>
        </div>
      </div>

      {/* Interactive Presentation Viewer Modal */}
      <PresentationViewer
        isOpen={isPresentationOpen}
        onClose={() => setIsPresentationOpen(false)}
        lessonTitle={lesson.title}
        courseTitle={course?.title}
        slidesJson={lesson.presentation_json}
      />

      {/* Focus Mode Distraction-Free Modal */}
      <FocusModeModal
        isOpen={isFocusModeOpen}
        onClose={() => setIsFocusModeOpen(false)}
        lessonTitle={lesson.title}
        courseTitle={course?.title}
        contentMarkdown={lesson.content_markdown}
      />
    </div>
  );
};
