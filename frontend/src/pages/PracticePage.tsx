import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ExerciseItem } from '../api/client';
import {
  Code2,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  Send,
  Loader2,
  Sparkles,
  HelpCircle,
} from 'lucide-react';

export const PracticePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedExerciseId, setSelectedExerciseId] = useState<number>(1);
  const [code, setCode] = useState<string>(
    '#include <iostream>\n\nint main() {\n    std::cout << "Hello, Second Brain AI!" << std::endl;\n    return 0;\n}'
  );
  const [language, setLanguage] = useState<string>('cpp');
  const [quizAnswer, setQuizAnswer] = useState<string>('');
  const [sandboxOutput, setSandboxOutput] = useState<{
    stdout: string;
    stderr: string;
    exit_code: number;
    time_ms: number;
  } | null>(null);
  const [submissionResult, setSubmissionResult] = useState<{
    is_correct: boolean;
    score: number;
    feedback: string;
    next_review_in_days: number;
  } | null>(null);

  const { data: exercises = [], isLoading } = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api.getExercises(),
  });

  const selectedExercise = exercises.find((e) => e.id === selectedExerciseId) || exercises[0];

  const runCodeMutation = useMutation({
    mutationFn: () => api.runCode(language, code),
    onSuccess: (data) => {
      setSandboxOutput({
        stdout: data.stdout,
        stderr: data.stderr,
        exit_code: data.exit_code,
        time_ms: data.execution_time_ms,
      });
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      const answer = selectedExercise?.exercise_type === 'code' ? code : quizAnswer;
      return api.submitExercise(selectedExercise.id, answer);
    },
    onSuccess: (data) => {
      setSubmissionResult(data);
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      queryClient.invalidateQueries({ queryKey: ['dueReviews'] });
    },
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Code2 className="w-6 h-6 text-brand-indigo" />
          <span>Практика и изолированная песочница Linux</span>
        </h1>
        <p className="text-xs text-slate-400">
          Безопасное изолированное выполнение программ на C++, Python, Bash с проверкой и интервальным повторением
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Exercise List */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-sm font-bold text-white">Доступные задания</h3>
          {isLoading ? (
            <div className="flex justify-center p-6">
              <Loader2 className="w-6 h-6 animate-spin text-brand-indigo" />
            </div>
          ) : (
            <div className="space-y-2">
              {exercises.map((ex) => (
                <div
                  key={ex.id}
                  onClick={() => {
                    setSelectedExerciseId(ex.id);
                    setSubmissionResult(null);
                    setSandboxOutput(null);
                    if (ex.exercise_type === 'code') {
                      setCode(ex.initial_code || code);
                    }
                  }}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-1.5 ${
                    selectedExercise?.id === ex.id
                      ? 'bg-graphite-800 border-brand-indigo shadow-md'
                      : 'bg-graphite-900/80 border-graphite-700/60 hover:bg-graphite-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{ex.title}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-graphite-700 text-slate-300">
                      {ex.exercise_type === 'code' ? 'Код' : 'Тест'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2">{ex.prompt}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Workspace & Sandbox Runner */}
        <div className="lg:col-span-2 space-y-6">
          {selectedExercise && (
            <div className="p-6 rounded-2xl bg-graphite-900 border border-graphite-700/80 space-y-4 shadow-xl">
              <div>
                <div className="flex items-center gap-2 text-xs text-brand-indigo font-bold uppercase tracking-wider">
                  <span>Задание: {selectedExercise.title}</span>
                  <span>•</span>
                  <span>Сложность: {selectedExercise.difficulty}</span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">{selectedExercise.prompt}</h2>
              </div>

              {selectedExercise.exercise_type === 'code' ? (
                /* Code Editor & Sandbox */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400">Язык:</span>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="bg-graphite-800 border border-graphite-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-brand-indigo font-semibold"
                      >
                        <option value="cpp">C++ (g++ 16 / C++20)</option>
                        <option value="python">Python 3.14</option>
                        <option value="bash">Bash</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => runCodeMutation.mutate()}
                        disabled={runCodeMutation.isPending}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-graphite-800 hover:bg-graphite-700 border border-graphite-700 text-slate-200 text-xs font-semibold shadow transition-all disabled:opacity-50"
                      >
                        {runCodeMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Play className="w-3.5 h-3.5 fill-current text-brand-emerald" />
                        )}
                        <span>Запустить код</span>
                      </button>

                      <button
                        onClick={() => submitMutation.mutate()}
                        disabled={submitMutation.isPending}
                        className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                      >
                        {submitMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        <span>Отправить на проверку</span>
                      </button>
                    </div>
                  </div>

                  {/* Code Editor */}
                  <textarea
                    rows={12}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full bg-graphite-950 border border-graphite-700/90 rounded-xl p-4 font-mono text-xs text-emerald-300 leading-relaxed focus:outline-none focus:border-brand-indigo shadow-inner"
                    spellCheck={false}
                  />

                  {/* Terminal Console Output */}
                  {sandboxOutput && (
                    <div className="rounded-xl bg-black border border-graphite-800 overflow-hidden shadow-inner">
                      <div className="p-2.5 bg-graphite-950 border-b border-graphite-800 flex items-center justify-between text-xs text-slate-400">
                        <span className="flex items-center gap-2 font-mono">
                          <Terminal className="w-3.5 h-3.5 text-brand-indigo" />
                          <span>Консоль вывода (sandbox)</span>
                        </span>
                        <span>
                          {sandboxOutput.time_ms} мс • Код возврата: {sandboxOutput.exit_code}
                        </span>
                      </div>
                      <div className="p-4 font-mono text-xs max-h-48 overflow-y-auto space-y-2">
                        {sandboxOutput.stdout && (
                          <pre className="text-slate-200 whitespace-pre-wrap">{sandboxOutput.stdout}</pre>
                        )}
                        {sandboxOutput.stderr && (
                          <pre className="text-red-400 whitespace-pre-wrap">{sandboxOutput.stderr}</pre>
                        )}
                        {!sandboxOutput.stdout && !sandboxOutput.stderr && (
                          <span className="text-slate-600 italic">Программа завершилась без вывода.</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Quiz Form */
                <div className="space-y-4 pt-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-2">Ваш ответ:</label>
                    <input
                      type="text"
                      value={quizAnswer}
                      onChange={(e) => setQuizAnswer(e.target.value)}
                      placeholder="Введите число, слово или символ..."
                      className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
                    />
                  </div>

                  <button
                    onClick={() => submitMutation.mutate()}
                    disabled={!quizAnswer.trim() || submitMutation.isPending}
                    className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-xs shadow-md transition-all disabled:opacity-50"
                  >
                    {submitMutation.isPending ? 'Проверка...' : 'Проверить ответ'}
                  </button>
                </div>
              )}

              {/* Feedback and Spaced Repetition Scheduling Alert */}
              {submissionResult && (
                <div
                  className={`p-4 rounded-xl border space-y-1.5 text-xs ${
                    submissionResult.is_correct
                      ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-200'
                      : 'bg-amber-950/40 border-amber-800/80 text-amber-200'
                  }`}
                >
                  <div className="flex items-center gap-2 font-bold text-sm">
                    {submissionResult.is_correct ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span>Результат: Верно (100 баллов)</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-amber-400" />
                        <span>Результат: Требует внимания</span>
                      </>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap">{submissionResult.feedback}</p>
                  <p className="text-[11px] text-slate-400 pt-1">
                    Интервальное повторение SM-2: следующее закрепление запланировано через{' '}
                    <span className="font-bold text-white">{submissionResult.next_review_in_days} дн.</span>
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
