import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, getUserId, setUserId, getUserName, setUserName } from '../../api/client';
import { Play, Sparkles, Menu, User, Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onOpenMobileMenu }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [inputUserId, setInputUserId] = useState(getUserId());
  const [inputUserName, setInputUserName] = useState(getUserName());

  const { data: session } = useQuery({
    queryKey: ['lastActiveSession'],
    queryFn: api.getLastActiveSession,
  });

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
  });

  const getModeLabel = (mode?: string) => {
    switch (mode) {
      case 'only_my_materials':
        return 'Только мои материалы';
      case 'my_materials_plus_ai':
        return 'Мои материалы + ИИ';
      default:
        return 'Свободное обучение';
    }
  };

  const handleResume = () => {
    if (session?.has_active_session && session.lesson_id) {
      navigate(`/courses/${session.course_id}/lessons/${session.lesson_id}`);
    } else if (session?.course_id) {
      navigate(`/courses/${session.course_id}`);
    } else {
      navigate('/courses');
    }
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUserId.trim()) {
      setUserId(inputUserId.trim());
      setUserName(inputUserName.trim() || 'Студент');
      setIsUserModalOpen(false);
      // Invalidate queries so courses and dashboard reload for this user
      queryClient.invalidateQueries();
    }
  };

  return (
    <header className="h-16 border-b border-graphite-700/60 bg-graphite-900/80 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3 min-w-0">
        {/* Mobile Hamburger Button */}
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden p-2 rounded-xl bg-graphite-800 hover:bg-graphite-700 text-slate-300 hover:text-white border border-graphite-700 shrink-0 transition-colors"
          title="Открыть панель задач"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-base sm:text-lg font-bold text-white tracking-tight truncate">{title}</h2>
            {/* Signature badge in Header */}
            <span className="inline-flex items-center text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-brand-purple/15 text-purple-300 border border-brand-purple/30 shrink-0">
              Made by Mirzo
            </span>
          </div>
          {subtitle && <p className="text-[11px] text-slate-400 truncate hidden sm:block">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 shrink-0">
        {/* Learning Mode Badge */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full bg-graphite-800/90 border border-graphite-700 text-xs text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
          <span>Режим:</span>
          <span className="font-medium text-white">{getModeLabel(settings?.default_learning_mode)}</span>
        </div>

        {/* Quick Continue Button */}
        {session?.has_active_session && (
          <button
            onClick={handleResume}
            className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all active:scale-95"
            title={session.welcome_message}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span className="hidden sm:inline">Продолжить</span>
            <span className="text-indigo-200 truncate max-w-[100px] sm:max-w-[140px] font-normal">
              {session.lesson_title || session.course_title}
            </span>
          </button>
        )}

        {/* User Account Button */}
        <button
          onClick={() => {
            setInputUserId(getUserId());
            setInputUserName(getUserName());
            setIsUserModalOpen(true);
          }}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-graphite-800 hover:bg-graphite-700 border border-graphite-700 text-xs text-slate-300 hover:text-white transition-all"
          title="Мой профиль и переключение аккаунта"
        >
          <User className="w-3.5 h-3.5 text-brand-indigo" />
          <span className="hidden md:inline font-medium">{getUserName()}</span>
        </button>
      </div>

      {/* User Profile Modal */}
      {isUserModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-graphite-900 border border-graphite-700/80 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-graphite-700/60">
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-brand-indigo" />
                <h3 className="text-base font-bold text-white">Профиль пользователя</h3>
              </div>
              <button
                onClick={() => setIsUserModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Ваши курсы, заметки и история диалогов привязаны к вашему ID. Другие пользователи не видят ваши материалы.
            </p>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Имя пользователя
                </label>
                <input
                  type="text"
                  value={inputUserName}
                  onChange={(e) => setInputUserName(e.target.value)}
                  placeholder="Например: Mirzo"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-graphite-950 border border-graphite-700 text-white text-xs focus:outline-none focus:border-brand-indigo"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  ID аккаунта (для синхронизации между устройствами)
                </label>
                <input
                  type="text"
                  value={inputUserId}
                  onChange={(e) => setInputUserId(e.target.value)}
                  placeholder="usr_..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-graphite-950 border border-graphite-700 text-white font-mono text-xs focus:outline-none focus:border-brand-indigo"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Введите одинаковый ID на телефоне и компьютере, чтобы иметь общий доступ к своим курсам.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUserModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-xs shadow-md shadow-indigo-500/20"
                >
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
