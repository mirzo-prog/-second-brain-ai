import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { CalendarCheck, Clock, CheckCircle2, RotateCcw, Sparkles, Loader2 } from 'lucide-react';

export const StudyPlanPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeReviewId, setActiveReviewId] = useState<number | null>(null);

  const { data: dueItems = [], isLoading } = useQuery({
    queryKey: ['dueReviews'],
    queryFn: api.getDueReviews,
  });

  const gradeMutation = useMutation({
    mutationFn: ({ id, grade }: { id: number; grade: number }) => api.gradeReview(id, grade),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dueReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setActiveReviewId(null);
    },
  });

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <CalendarCheck className="w-6 h-6 text-brand-indigo" />
          <span>План обучения и интервальные повторения (SM-2)</span>
        </h1>
        <p className="text-xs text-slate-400">
          Научный алгоритм кривой забывания Эббингауза для долговременной фиксации знаний
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-amber" />
          <span>Повторения, запланированные на сегодня ({dueItems.length})</span>
        </h3>

        {isLoading ? (
          <div className="flex justify-center p-8">
            <Loader2 className="w-6 h-6 animate-spin text-brand-indigo" />
          </div>
        ) : dueItems.length > 0 ? (
          <div className="space-y-3">
            {dueItems.map((item) => (
              <div
                key={item.id}
                className="p-5 rounded-2xl bg-graphite-900 border border-graphite-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                    Тип: {item.item_type} • Повторений: {item.repetitions}
                  </span>
                  <h4 className="text-sm font-bold text-white">{item.title}</h4>
                  <p className="text-xs text-slate-400">
                    Текущий интервал: {item.interval_days} дн. (Фактор легкости: {item.ease_factor})
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => gradeMutation.mutate({ id: item.id, grade: 1 })}
                    disabled={gradeMutation.isPending}
                    className="px-3 py-1.5 rounded-lg bg-red-950/60 hover:bg-red-900 text-red-300 border border-red-800 text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    Забыл (1 дн.)
                  </button>
                  <button
                    onClick={() => gradeMutation.mutate({ id: item.id, grade: 3 })}
                    disabled={gradeMutation.isPending}
                    className="px-3 py-1.5 rounded-lg bg-amber-950/60 hover:bg-amber-900 text-amber-300 border border-amber-800 text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    С трудом
                  </button>
                  <button
                    onClick={() => gradeMutation.mutate({ id: item.id, grade: 5 })}
                    disabled={gradeMutation.isPending}
                    className="px-4 py-1.5 rounded-lg bg-brand-emerald hover:bg-emerald-600 text-white text-xs font-semibold shadow transition-colors disabled:opacity-50"
                  >
                    Помню отлично
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-graphite-900/40 border border-dashed border-graphite-700 text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-brand-emerald mx-auto" />
            <h4 className="font-bold text-white text-sm">Все повторения на сегодня завершены!</h4>
            <p className="text-xs text-slate-400">
              Новые элементы появятся здесь автоматически в соответствии с расписанием алгоритма SM-2.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
