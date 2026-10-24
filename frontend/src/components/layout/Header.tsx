import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Play, Sparkles, Menu, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onOpenMobileMenu }) => {
  const navigate = useNavigate();
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
            <span className="hidden lg:inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-purple/15 text-purple-300 border border-brand-purple/30 shrink-0">
              <Heart className="w-2.5 h-2.5 text-red-400 fill-current" />
              <span>Made by Mirzo</span>
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
      </div>
    </header>
  );
};
