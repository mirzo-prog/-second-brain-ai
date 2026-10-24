import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  Bot,
  User,
  Send,
  Sparkles,
  Paperclip,
  BookOpen,
  Info,
  HelpCircle,
  Code2,
  RefreshCw,
  Loader2,
} from 'lucide-react';

interface ChatMessage {
  id?: number;
  sender: 'user' | 'assistant';
  content: string;
  sources_used?: string[];
  is_rag_sourced?: boolean;
}

export const TutorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialCourseId = parseInt(searchParams.get('courseId') || '0', 10);
  const initialLessonId = parseInt(searchParams.get('lessonId') || '0', 10);

  const [selectedCourseId, setSelectedCourseId] = useState<number>(initialCourseId);
  const [selectedLessonId, setSelectedLessonId] = useState<number>(initialLessonId);
  const [learningMode, setLearningMode] = useState<string>('free');
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const promptSentRef = useRef<boolean>(false);

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: () => api.getCourses(false),
  });

  const { data: courseDetail } = useQuery({
    queryKey: ['courseDetail', selectedCourseId],
    queryFn: () => api.getCourseDetail(selectedCourseId),
    enabled: selectedCourseId > 0,
  });

  useEffect(() => {
    if (courses.length > 0 && selectedCourseId === 0) {
      setSelectedCourseId(courses[0].id);
    }
  }, [courses, selectedCourseId]);

  useEffect(() => {
    if (courseDetail) {
      setLearningMode(courseDetail.learning_mode || 'free');
    }
  }, [courseDetail]);

  // Handle incoming prompt query parameter from lesson page
  useEffect(() => {
    const promptParam = searchParams.get('prompt');
    if (promptParam && selectedCourseId > 0 && !promptSentRef.current) {
      promptSentRef.current = true;
      chatMutation.mutate(promptParam);
    }
  }, [searchParams, selectedCourseId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (msg: string) =>
      api.sendChatMessage({
        course_id: selectedCourseId,
        lesson_id: selectedLessonId > 0 ? selectedLessonId : undefined,
        message: msg,
        learning_mode: learningMode,
      }),
    onMutate: (newMsg) => {
      setMessages((prev) => [...prev, { sender: 'user', content: newMsg }]);
      setInputMessage('');
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: data.message_id,
          sender: 'assistant',
          content: data.content,
          sources_used: data.sources_used,
          is_rag_sourced: data.is_rag_sourced,
        },
      ]);
    },
    onError: (err: any) => {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          content: `Произошла ошибка при обращении к ИИ-преподавателю: ${err.message}`,
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!inputMessage.trim() || selectedCourseId === 0) return;
    chatMutation.mutate(inputMessage.trim());
  };

  const quickPrompts = [
    'Я не понимаю эту тему, объясни проще на аналогии.',
    'Приведи подробный практический пример кода.',
    'Дай мне маленькое проверочное задание.',
    'В чем типичные ошибки новичков здесь?',
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto flex flex-col h-[calc(100vh-5rem)]">
      {/* Controls Bar */}
      <div className="p-4 rounded-2xl bg-graphite-900 border border-graphite-700/80 mb-4 flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-md">
        <div className="flex flex-wrap items-center gap-3">
          {/* Course selector */}
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-brand-indigo" />
            <select
              value={selectedCourseId}
              onChange={(e) => {
                setSelectedCourseId(parseInt(e.target.value, 10));
                setSelectedLessonId(0);
              }}
              className="bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-brand-indigo font-medium"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>

          {/* Lesson selector */}
          {courseDetail && courseDetail.modules && (
            <select
              value={selectedLessonId}
              onChange={(e) => setSelectedLessonId(parseInt(e.target.value, 10))}
              className="bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-brand-indigo max-w-xs truncate"
            >
              <option value="0">Все темы курса (общий контекст)</option>
              {courseDetail.modules.flatMap((m) =>
                m.lessons.map((l) => (
                  <option key={l.id} value={l.id}>
                    {m.title}: {l.title}
                  </option>
                ))
              )}
            </select>
          )}
        </div>

        {/* Learning Mode Switcher */}
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
          <span className="text-xs text-slate-400 font-medium">Режим:</span>
          <select
            value={learningMode}
            onChange={(e) => setLearningMode(e.target.value)}
            className="bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-brand-indigo font-semibold"
          >
            <option value="free">Свободное обучение</option>
            <option value="my_materials_plus_ai">Мои материалы + знания ИИ</option>
            <option value="only_my_materials">Только мои материалы</option>
          </select>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 bg-graphite-900/80 border border-graphite-700/60 rounded-2xl p-6 overflow-y-auto space-y-4 shadow-inner">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 text-slate-400">
            <div className="w-16 h-16 rounded-2xl bg-brand-indigo/15 border border-brand-indigo/30 flex items-center justify-center text-brand-indigo">
              <Bot className="w-8 h-8" />
            </div>
            <div className="max-w-md space-y-1">
              <h3 className="font-bold text-white text-base">ИИ-преподаватель готов к занятию</h3>
              <p className="text-xs text-slate-400">
                Задайте вопрос, попросите объяснить сложную тему или выберите подсказку ниже.
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full pt-4">
              {quickPrompts.map((qp, i) => (
                <button
                  key={i}
                  onClick={() => chatMutation.mutate(qp)}
                  className="p-3 text-left rounded-xl bg-graphite-800/80 hover:bg-graphite-800 border border-graphite-700/60 hover:border-brand-indigo/50 text-xs text-slate-300 transition-all"
                >
                  {qp}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3.5 max-w-3xl ${
                msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-brand-blue text-white'
                    : 'bg-gradient-to-tr from-brand-indigo to-brand-purple text-white'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed space-y-2 shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-brand-indigo text-white rounded-tr-none'
                    : 'bg-graphite-800 border border-graphite-700 text-slate-200 rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citations Badges */}
                {msg.sources_used && msg.sources_used.length > 0 && (
                  <div className="pt-2 border-t border-graphite-700/60 flex flex-wrap gap-1.5">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block w-full">
                      Использованные источники:
                    </span>
                    {msg.sources_used.map((src, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 rounded bg-brand-indigo/20 border border-brand-indigo/40 text-[11px] text-indigo-300 font-medium"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {chatMutation.isPending && (
          <div className="flex gap-3 max-w-xl mr-auto items-center text-xs text-slate-400 p-3 rounded-xl bg-graphite-800 border border-graphite-700">
            <Loader2 className="w-4 h-4 animate-spin text-brand-indigo" />
            <span>ИИ-преподаватель анализирует вопрос и готовит понятный ответ...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="pt-4 flex gap-3 shrink-0">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Спросите что угодно по уроку или теме курса..."
          className="flex-1 bg-graphite-900 border border-graphite-700/80 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo transition-colors shadow-sm"
        />
        <button
          onClick={handleSend}
          disabled={!inputMessage.trim() || chatMutation.isPending}
          className="px-5 py-3 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold flex items-center justify-center gap-2 shadow-md disabled:opacity-50 transition-all active:scale-95 shrink-0"
        >
          <Send className="w-4 h-4" />
          <span>Отправить</span>
        </button>
      </div>
    </div>
  );
};
