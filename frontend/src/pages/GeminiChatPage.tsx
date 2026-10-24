import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ChatSessionSummary, ChatMessageItem } from '../api/client';
import {
  Sparkles,
  Send,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Copy,
  RotateCcw,
  Bot,
  User,
  MessageSquare,
  Loader2,
  Menu,
  ChevronRight,
} from 'lucide-react';

export const GeminiChatPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [inputText, setInputText] = useState('');
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [editingTitleId, setEditingTitleId] = useState<number | null>(null);
  const [editTitleValue, setEditTitleValue] = useState('');
  const [showHistoryMobile, setShowHistoryMobile] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // 1. Fetch user's chat sessions
  const { data: sessions = [], isLoading: isLoadingSessions } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: api.getChatSessions,
  });

  // Select the latest session on first load if none selected
  useEffect(() => {
    if (sessions.length > 0 && activeSessionId === null) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  // 2. Fetch messages of active session
  const {
    data: activeSession,
    isLoading: isLoadingMessages,
    refetch: refetchSession,
  } = useQuery({
    queryKey: ['chatSession', activeSessionId],
    queryFn: () => (activeSessionId ? api.getChatSession(activeSessionId) : null),
    enabled: !!activeSessionId,
  });

  const messages = activeSession?.messages || [];

  // Scroll to bottom when new messages arrive and autoScroll is active
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Detect user scroll to pause/resume autoScroll
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 80;
    setAutoScroll(isNearBottom);
  };

  // 3. Mutations
  const createSessionMutation = useMutation({
    mutationFn: () => api.createChatSession(),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      setActiveSessionId(newSession.id);
      setShowHistoryMobile(false);
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      api.renameChatSession(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      queryClient.invalidateQueries({ queryKey: ['chatSession', activeSessionId] });
      setEditingTitleId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteChatSession(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      if (activeSessionId === deletedId) {
        setActiveSessionId(null);
      }
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, text }: { sessionId: number; text: string }) =>
      api.sendFreeChatMessage(sessionId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSession', activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      setAutoScroll(true);
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: (sessionId: number) => api.regenerateFreeChatMessage(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSession', activeSessionId] });
      setAutoScroll(true);
    },
  });

  // Handle Send
  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputText.trim();
    if (!text || sendMessageMutation.isPending) return;

    setInputText('');

    if (!activeSessionId) {
      // Create session first
      const newSession = await api.createChatSession(text.slice(0, 35));
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      setActiveSessionId(newSession.id);
      sendMessageMutation.mutate({ sessionId: newSession.id, text });
    } else {
      sendMessageMutation.mutate({ sessionId: activeSessionId, text });
    }
  };

  const handleCopy = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const starterChips = [
    'Объясни теорию относительности простыми словами',
    'Посоветуй 5 выдающихся книг по философии и истории',
    'Помоги разобраться в алгоритмах быстрой сортировки',
    'Давай обсудим идеи искусственного интеллекта будущего',
  ];

  return (
    <div className="h-[calc(100vh-4.5rem)] flex overflow-hidden">
      {/* Mobile Drawer Backdrop */}
      {showHistoryMobile && (
        <div
          onClick={() => setShowHistoryMobile(false)}
          className="fixed inset-0 bg-black/60 z-30 md:hidden backdrop-blur-xs"
        />
      )}

      {/* Left Sidebar: Chat Sessions History */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 md:z-0 w-72 bg-graphite-900 border-r border-graphite-700/70 flex flex-col transition-transform duration-300 ${
          showHistoryMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="p-4 border-b border-graphite-700/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-purple" />
            <h2 className="text-sm font-bold text-white tracking-wide">Gemini Chat</h2>
          </div>
          <button
            onClick={() => createSessionMutation.mutate()}
            disabled={createSessionMutation.isPending}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-brand-indigo/20 hover:bg-brand-indigo/30 border border-brand-indigo/40 text-indigo-300 text-xs font-semibold transition-all"
            title="Создать новый диалог"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Новый</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoadingSessions ? (
            <div className="p-6 flex justify-center">
              <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              Нет диалогов. Нажмите «Новый», чтобы начать беседу.
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.id === activeSessionId;
              const isEditing = editingTitleId === s.id;

              return (
                <div
                  key={s.id}
                  onClick={() => {
                    if (!isEditing) {
                      setActiveSessionId(s.id);
                      setShowHistoryMobile(false);
                    }
                  }}
                  className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-brand-indigo/20 text-white border border-brand-indigo/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-graphite-800/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1 mr-2">
                    <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-brand-indigo' : 'text-slate-500'}`} />
                    {isEditing ? (
                      <input
                        type="text"
                        value={editTitleValue}
                        onChange={(e) => setEditTitleValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            renameMutation.mutate({ id: s.id, title: editTitleValue });
                          } else if (e.key === 'Escape') {
                            setEditingTitleId(null);
                          }
                        }}
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                        className="bg-graphite-950 border border-brand-indigo rounded px-1.5 py-0.5 text-xs text-white w-full outline-none"
                      />
                    ) : (
                      <span className="truncate">{s.title}</span>
                    )}
                  </div>

                  {/* Actions on hover/active */}
                  <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    {isEditing ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            renameMutation.mutate({ id: s.id, title: editTitleValue });
                          }}
                          className="p-1 hover:text-green-400 text-slate-400"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingTitleId(null);
                          }}
                          className="p-1 hover:text-red-400 text-slate-400"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingTitleId(s.id);
                            setEditTitleValue(s.title);
                          }}
                          className="p-1 hover:text-white text-slate-500"
                          title="Переименовать"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`Удалить диалог «${s.title}»?`)) {
                              deleteMutation.mutate(s.id);
                            }
                          }}
                          className="p-1 hover:text-red-400 text-slate-500"
                          title="Удалить"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col bg-graphite-950 min-w-0">
        {/* Top Chat Header */}
        <header className="px-6 py-3.5 border-b border-graphite-800 bg-graphite-900/50 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setShowHistoryMobile(true)}
              className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-graphite-800"
              title="Список диалогов"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="min-w-0">
              <h1 className="text-sm font-bold text-white truncate flex items-center gap-2">
                {activeSession?.title || 'Свободное общение с Gemini'}
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-purple/20 text-purple-300 border border-brand-purple/30">
                  Google Gemini AI
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 truncate">
                Обсуждайте книги, идеи, науку, код и повседневные вопросы
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => createSessionMutation.mutate()}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-graphite-800 hover:bg-graphite-700 text-xs font-medium text-slate-300 hover:text-white border border-graphite-700 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Новый чат</span>
            </button>
          </div>
        </header>

        {/* Messages Scroll Area */}
        <div
          ref={chatContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5"
        >
          {isLoadingMessages ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-brand-indigo animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6 max-w-xl mx-auto text-slate-400">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-blue via-brand-indigo to-brand-purple flex items-center justify-center text-white shadow-xl shadow-indigo-500/20">
                <Sparkles className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-lg font-bold text-white">Чем Gemini может помочь сегодня?</h3>
                <p className="text-xs text-slate-400">
                  Задайте любой вопрос, попросите объяснить сложную идею или обсудите интересную тему.
                </p>
              </div>

              {/* Quick starter chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full pt-2">
                {starterChips.map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputText(chip);
                    }}
                    className="p-3 text-left rounded-xl bg-graphite-900/90 hover:bg-graphite-800 border border-graphite-700/60 hover:border-brand-indigo/50 text-xs text-slate-300 transition-all flex items-start gap-2 shadow-sm"
                  >
                    <ChevronRight className="w-3.5 h-3.5 text-brand-indigo shrink-0 mt-0.5" />
                    <span>{chip}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
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

                <div className="space-y-1.5 group max-w-[85%]">
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed shadow-md ${
                      msg.sender === 'user'
                        ? 'bg-brand-indigo text-white rounded-tr-none'
                        : 'bg-graphite-900 border border-graphite-700/80 text-slate-200 rounded-tl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
                  </div>

                  {/* Actions under message */}
                  <div
                    className={`flex items-center gap-2 text-[11px] text-slate-500 px-1 opacity-0 group-hover:opacity-100 transition-opacity ${
                      msg.sender === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <button
                      onClick={() => handleCopy(msg.content, msg.id)}
                      className="hover:text-slate-300 flex items-center gap-1 transition-colors"
                      title="Скопировать"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-3 h-3 text-green-400" />
                          <span className="text-green-400">Скопировано</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Копировать</span>
                        </>
                      )}
                    </button>

                    {msg.sender === 'assistant' && (
                      <button
                        onClick={() => {
                          if (activeSessionId) {
                            regenerateMutation.mutate(activeSessionId);
                          }
                        }}
                        disabled={regenerateMutation.isPending}
                        className="hover:text-slate-300 flex items-center gap-1 transition-colors ml-2"
                        title="Сгенерировать ответ заново"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Перегенерировать</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {sendMessageMutation.isPending && (
            <div className="flex gap-3.5 max-w-3xl mr-auto">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-indigo to-brand-purple text-white flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="p-4 rounded-2xl bg-graphite-900 border border-graphite-700/80 text-slate-300 rounded-tl-none flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-brand-indigo animate-spin" />
                <span className="text-xs text-slate-400">Gemini думает...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-graphite-800 bg-graphite-900/60 shrink-0">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={2}
              placeholder="Спросите у Gemini что угодно... (Enter для отправки, Shift+Enter для новой строки)"
              className="flex-1 bg-graphite-950 border border-graphite-700/80 rounded-2xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo resize-none transition-all"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || sendMessageMutation.isPending}
              className="self-end px-5 py-3 rounded-2xl bg-gradient-to-r from-brand-blue via-brand-indigo to-brand-purple hover:from-blue-600 hover:to-purple-600 text-white font-semibold text-sm shadow-md shadow-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95 flex items-center justify-center"
            >
              {sendMessageMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
