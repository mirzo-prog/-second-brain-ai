import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Play, Sparkles, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
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
        return 'Мои материалы + знания ИИ';
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
    <header className="h-16 border-b border-graphite-700/60 bg-graphite-900/60 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Learning Mode Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-graphite-800/90 border border-graphite-700 text-xs text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
          <span>Режим:</span>
          <span className="font-medium text-white">{getModeLabel(settings?.default_learning_mode)}</span>
        </div>

        {/* Quick Continue Button */}
        {session?.has_active_session && (
          <button
            onClick={handleResume}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all active:scale-95"
            title={session.welcome_message}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Продолжить</span>
            <span className="text-indigo-200 truncate max-w-[140px] font-normal">
              ({session.lesson_title || session.course_title})
            </span>
          </button>
        )}
      </div>
    </header>
  );
};
