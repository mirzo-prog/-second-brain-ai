import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { BarChart3, Clock, CheckCircle2, Award, BookOpen, Layers, Loader2 } from 'lucide-react';

export const StatisticsPage: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['statistics'],
    queryFn: api.getStatistics,
  });

  if (isLoading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-[500px]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-indigo" />
      </div>
    );
  }

  const dailyData = stats?.daily_study_time || [];
  const skillsData = stats?.skills_breakdown || [];

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-brand-indigo" />
          <span>Аналитика и статистика прогресса</span>
        </h1>
        <p className="text-xs text-slate-400">
          Точные показатели учебного времени, точности тестирования и распределения навыков
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 space-y-1">
          <p className="text-xs text-slate-400">Всего часов обучения</p>
          <h3 className="text-2xl font-bold text-white">{stats?.total_study_hours || 0} ч</h3>
        </div>

        <div className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 space-y-1">
          <p className="text-xs text-slate-400">Точность в тестах</p>
          <h3 className="text-2xl font-bold text-emerald-400">{stats?.accuracy_percentage || 0}%</h3>
        </div>

        <div className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 space-y-1">
          <p className="text-xs text-slate-400">Пройдено уроков</p>
          <h3 className="text-2xl font-bold text-white">
            {stats?.completed_lessons || 0} <span className="text-xs text-slate-500 font-normal">/ {stats?.total_lessons || 0}</span>
          </h3>
        </div>

        <div className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 space-y-1">
          <p className="text-xs text-slate-400">Закреплено повторений</p>
          <h3 className="text-2xl font-bold text-indigo-400">{stats?.completed_reviews || 0}</h3>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Study Time Chart */}
        <div className="p-6 rounded-2xl bg-graphite-900 border border-graphite-700/80 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-brand-blue" />
            <span>Время занятий по дням (минуты)</span>
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="studyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="minutes" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#studyGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skills Mastery Breakdown Pie Chart */}
        <div className="p-6 rounded-2xl bg-graphite-900 border border-graphite-700/80 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Award className="w-4 h-4 text-brand-purple" />
            <span>Распределение статусов навыков</span>
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={skillsData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {skillsData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
