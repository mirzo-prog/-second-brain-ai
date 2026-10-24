import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, SkillItem } from '../api/client';
import { Award, CheckCircle2, Clock, AlertTriangle, ChevronRight, Loader2 } from 'lucide-react';

export const SkillsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: skills = [], isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: api.getSkills,
  });

  const updateSkillMutation = useMutation({
    mutationFn: ({ id, status, confidence }: { id: number; status: string; confidence: number }) =>
      api.updateSkillProgress(id, status, confidence),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['skillGraph'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  // Group by category
  const categories = Array.from(new Set(skills.map((s) => s.category)));

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'mastered':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">Освоено</span>;
      case 'learning':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-950 text-blue-400 border border-blue-800">Изучается</span>;
      case 'needs_practice':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">Требует практики</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">Не начато</span>;
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Award className="w-6 h-6 text-brand-indigo" />
          <span>Трекер подтверждённых навыков</span>
        </h1>
        <p className="text-xs text-slate-400">
          Отслеживание реального владения технологиями на основе тестов, практики и повторений
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-brand-indigo" />
        </div>
      ) : (
        <div className="space-y-8">
          {categories.map((cat) => {
            const catSkills = skills.filter((s) => s.category === cat);
            return (
              <div key={cat} className="space-y-4">
                <h3 className="text-base font-bold text-indigo-300 border-b border-graphite-700/60 pb-2">
                  {cat} ({catSkills.length})
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {catSkills.map((skill) => (
                    <div
                      key={skill.id}
                      className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 space-y-3 shadow-sm hover:border-graphite-600 transition-all"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h4 className="font-bold text-sm text-white">{skill.name}</h4>
                          {skill.description && (
                            <p className="text-xs text-slate-400 mt-0.5">{skill.description}</p>
                          )}
                        </div>
                        {getStatusBadge(skill.status)}
                      </div>

                      {/* Confidence Level Bar */}
                      <div className="space-y-1.5 pt-2 border-t border-graphite-700/40">
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>Уверенность владения:</span>
                          <span className="font-bold text-white">{skill.confidence_level}%</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={skill.confidence_level}
                          onChange={(e) => {
                            const val = parseInt(e.target.value, 10);
                            let st = skill.status;
                            if (val === 100) st = 'mastered';
                            else if (val >= 60) st = 'needs_practice';
                            else if (val > 0) st = 'learning';
                            else st = 'not_started';
                            updateSkillMutation.mutate({ id: skill.id, status: st, confidence: val });
                          }}
                          className="w-full h-1.5 bg-graphite-700 rounded-lg appearance-none cursor-pointer accent-brand-indigo"
                        />
                      </div>

                      {/* Prerequisites */}
                      {skill.prerequisites && skill.prerequisites.length > 0 && (
                        <div className="text-[11px] text-slate-500 pt-1">
                          <span>Требует: </span>
                          <span className="text-slate-400">{skill.prerequisites.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
