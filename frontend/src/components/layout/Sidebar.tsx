import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Bot,
  Library,
  Network,
  Code2,
  Award,
  BarChart3,
  CalendarCheck,
  Settings,
  Brain,
  ShieldCheck,
  X,
  ChevronLeft,
  MessageSquare,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Главная', icon: LayoutDashboard },
  { to: '/courses', label: 'Мои курсы', icon: BookOpen },
  { to: '/chat', label: 'ИИ-чат (Gemini)', icon: MessageSquare },
  { to: '/tutor', label: 'ИИ-преподаватель', icon: Bot },
  { to: '/library', label: 'Библиотека', icon: Library },
  { to: '/knowledge-map', label: 'Карта знаний', icon: Network },
  { to: '/practice', label: 'Практика', icon: Code2 },
  { to: '/skills', label: 'Мои навыки', icon: Award },
  { to: '/statistics', label: 'Статистика', icon: BarChart3 },
  { to: '/study-plan', label: 'План обучения', icon: CalendarCheck },
  { to: '/settings', label: 'Настройки', icon: Settings },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Drawer */}
      <aside
        className={`fixed md:sticky top-0 h-screen bg-graphite-900 border-r border-graphite-700/60 flex flex-col z-50 transition-all duration-300 ease-in-out select-none shadow-2xl md:shadow-none ${
          // Mobile: slide in/out
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } ${
          // Desktop: collapse to icon width or expand
          isCollapsed ? 'md:w-20' : 'w-72 md:w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-graphite-700/60 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue via-brand-indigo to-brand-purple flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
              <Brain className="w-6 h-6 text-white" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0 truncate">
                <h1 className="font-bold text-sm tracking-wide text-white flex items-center gap-1.5 truncate">
                  Second Brain <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-indigo/30 text-brand-indigo border border-brand-indigo/40 font-semibold">AI</span>
                </h1>
                <p className="text-[11px] font-bold bg-gradient-to-r from-brand-blue via-brand-indigo to-brand-purple bg-clip-text text-transparent truncate">
                  Made by Mirzo
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1">
            {/* Desktop collapse toggle */}
            <button
              onClick={onToggleCollapse}
              className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-graphite-800 transition-colors"
              title={isCollapsed ? 'Развернуть панель' : 'Свернуть панель'}
            >
              <ChevronLeft className={`w-4 h-4 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`} />
            </button>

            {/* Mobile close button */}
            <button
              onClick={onClose}
              className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-graphite-800 transition-colors"
              title="Закрыть меню"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => {
                  // Auto-close drawer on mobile when clicking a link
                  if (window.innerWidth < 768) {
                    onClose();
                  }
                }}
                title={isCollapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-brand-indigo/25 to-brand-blue/15 text-white border-l-4 border-brand-indigo shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-graphite-800/80'
                  } ${isCollapsed ? 'justify-center px-0' : ''}`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer & Signature */}
        <div className="p-4 border-t border-graphite-700/60 bg-graphite-950/60 space-y-2.5">
          {!isCollapsed && (
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
                <span>Omarchy Linux</span>
              </span>
              <span className="text-slate-500 font-mono">127.0.0.1</span>
            </div>
          )}

          {/* MADE BY MIRZO SIGNATURE */}
          <div className="pt-2 border-t border-graphite-700/50 flex items-center justify-center text-xs">
            {!isCollapsed ? (
              <span className="text-xs font-extrabold tracking-wider bg-gradient-to-r from-brand-blue via-brand-indigo to-brand-purple bg-clip-text text-transparent uppercase">
                Made by Mirzo
              </span>
            ) : (
              <span className="text-[10px] font-black text-indigo-400 mx-auto" title="Made by Mirzo">
                M
              </span>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
