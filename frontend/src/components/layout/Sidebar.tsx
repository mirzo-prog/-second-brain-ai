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
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Главная', icon: LayoutDashboard },
  { to: '/courses', label: 'Мои курсы', icon: BookOpen },
  { to: '/tutor', label: 'ИИ-преподаватель', icon: Bot },
  { to: '/library', label: 'Библиотека', icon: Library },
  { to: '/knowledge-map', label: 'Карта знаний', icon: Network },
  { to: '/practice', label: 'Практика', icon: Code2 },
  { to: '/skills', label: 'Мои навыки', icon: Award },
  { to: '/statistics', label: 'Статистика', icon: BarChart3 },
  { to: '/study-plan', label: 'План обучения', icon: CalendarCheck },
  { to: '/settings', label: 'Настройки', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-graphite-900 border-r border-graphite-700/60 flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-graphite-700/60 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue via-brand-indigo to-brand-purple flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-wide text-white flex items-center gap-1.5">
            Second Brain <span className="text-xs px-1.5 py-0.5 rounded bg-brand-indigo/30 text-brand-indigo border border-brand-indigo/40 font-semibold">AI</span>
          </h1>
          <p className="text-xs text-slate-400">Интеллект обучения</p>
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
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-indigo/25 to-brand-blue/15 text-white border-l-4 border-brand-indigo shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-graphite-800/80'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Status */}
      <div className="p-4 border-t border-graphite-700/60 bg-graphite-950/40">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
            Omarchy Linux
          </span>
          <span className="text-slate-500 font-mono">localhost:8000</span>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-emerald" />
          <span>SQLite WAL • Изоляция</span>
        </div>
      </div>
    </aside>
  );
};
