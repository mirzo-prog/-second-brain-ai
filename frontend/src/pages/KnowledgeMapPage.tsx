import React, { useEffect, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Network, Award, ShieldCheck, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export const KnowledgeMapPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const { data: graphData, isLoading } = useQuery({
    queryKey: ['skillGraph'],
    queryFn: api.getSkillGraph,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (graphData) {
      const styledNodes = (graphData.nodes || []).map((n: any) => ({
        ...n,
        style: {
          background: '#111827',
          color: '#f8fafc',
          border: `2px solid ${n.data?.color || '#4f46e5'}`,
          borderRadius: '12px',
          padding: '12px',
          fontSize: '12px',
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          width: 220,
        },
      }));
      setNodes(styledNodes);
      setEdges(graphData.edges || []);
    }
  }, [graphData, setNodes, setEdges]);

  const updateSkillMutation = useMutation({
    mutationFn: ({ id, status, confidence }: { id: number; status: string; confidence: number }) =>
      api.updateSkillProgress(id, status, confidence),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skillGraph'] });
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  const getStatusLabel = (st?: string) => {
    switch (st) {
      case 'mastered':
        return 'Освоено (100%)';
      case 'learning':
        return 'Изучается';
      case 'needs_practice':
        return 'Требует практики';
      case 'needs_review':
        return 'Требует повторения';
      default:
        return 'Не начато';
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto flex flex-col h-[calc(100vh-5rem)]">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Network className="w-6 h-6 text-brand-indigo" />
            <span>Интерактивная карта знаний</span>
          </h1>
          <p className="text-xs text-slate-400">
            Визуальный граф взаимосвязей навыков, зависимостей и уровня мастерства
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs bg-graphite-900 border border-graphite-700/80 px-4 py-2 rounded-xl">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Освоено</span>
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <span>Изучается</span>
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Требует практики</span>
          </span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
            <span>Не начато</span>
          </span>
        </div>
      </div>

      {/* Main Flow Canvas & Details Drawer */}
      <div className="flex-1 flex gap-4 min-h-[480px]">
        {/* Canvas */}
        <div className="flex-1 rounded-2xl border border-graphite-700/70 overflow-hidden bg-graphite-950 shadow-inner relative">
          {isLoading ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-brand-indigo animate-spin" />
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={(_, node) => setSelectedNode(node)}
              fitView
            >
              <Background color="#334155" gap={20} size={1} />
              <Controls className="bg-graphite-800 border-graphite-700 fill-white" />
              <MiniMap
                nodeColor={(n) => n.data?.color || '#6366f1'}
                maskColor="rgba(15, 23, 42, 0.7)"
                className="bg-graphite-900 border border-graphite-700 rounded-xl"
              />
            </ReactFlow>
          )}
        </div>

        {/* Selected Skill Inspector Sidebar */}
        {selectedNode && (
          <div className="w-80 rounded-2xl bg-graphite-900 border border-graphite-700/80 p-5 space-y-4 shrink-0 shadow-xl overflow-y-auto">
            <div className="space-y-1">
              <span className="text-[10px] font-semibold tracking-wider uppercase text-indigo-400">
                {selectedNode.data?.category}
              </span>
              <h3 className="text-base font-bold text-white">{selectedNode.data?.label}</h3>
            </div>

            <div className="p-3 rounded-xl bg-graphite-800/80 border border-graphite-700 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Текущий статус:</span>
                <span className="font-bold text-white">{getStatusLabel(selectedNode.data?.status)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Уверенность:</span>
                <span className="font-bold text-brand-indigo">{selectedNode.data?.confidence}%</span>
              </div>
            </div>

            {/* Change Status Controls */}
            <div className="space-y-2 pt-2 border-t border-graphite-700/60">
              <label className="block text-xs font-medium text-slate-300">Изменить статус:</label>
              <div className="grid grid-cols-1 gap-1.5">
                {[
                  { key: 'learning', label: 'Изучается', conf: 40 },
                  { key: 'needs_practice', label: 'Требует практики', conf: 60 },
                  { key: 'mastered', label: 'Освоено (100%)', conf: 100 },
                  { key: 'not_started', label: 'Сбросить в «Не начато»', conf: 0 },
                ].map((s) => (
                  <button
                    key={s.key}
                    onClick={() =>
                      updateSkillMutation.mutate({
                        id: parseInt(selectedNode.id, 10),
                        status: s.key,
                        confidence: s.conf,
                      })
                    }
                    className="p-2 text-left rounded-lg bg-graphite-800 hover:bg-graphite-700 border border-graphite-700/50 text-xs text-slate-200 transition-colors"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => setSelectedNode(null)}
              className="w-full mt-4 py-2 rounded-lg bg-graphite-800 text-xs text-slate-400 hover:text-white"
            >
              Закрыть панель
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
