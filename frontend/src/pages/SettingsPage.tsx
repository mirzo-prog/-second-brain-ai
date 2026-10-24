import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  Settings,
  Key,
  Cpu,
  Database,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Save,
  RotateCcw,
  Download,
  Loader2,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash');
  const [ollamaUrl, setOllamaUrl] = useState('http://127.0.0.1:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3:latest');
  const [activeProvider, setActiveProvider] = useState('gemini');
  const [defaultMode, setDefaultMode] = useState('free');
  const [testStatus, setTestStatus] = useState<any>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
  });

  const { data: backups = [] } = useQuery({
    queryKey: ['backups'],
    queryFn: api.listBackups,
  });

  useEffect(() => {
    if (settings) {
      setGeminiModel(settings.gemini_model || 'gemini-2.5-flash');
      setOllamaUrl(settings.ollama_base_url || 'http://127.0.0.1:11434');
      setOllamaModel(settings.ollama_model || 'llama3:latest');
      setActiveProvider(settings.active_provider || 'gemini');
      setDefaultMode(settings.default_learning_mode || 'free');
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: () =>
      api.updateSettings({
        gemini_api_key: geminiKey ? geminiKey : undefined,
        gemini_model: geminiModel,
        ollama_base_url: ollamaUrl,
        ollama_model: ollamaModel,
        active_provider: activeProvider,
        default_learning_mode: defaultMode,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const testConnectionMutation = useMutation({
    mutationFn: api.testAIConnection,
    onSuccess: (res) => setTestStatus(res),
  });

  const backupMutation = useMutation({
    mutationFn: api.createBackup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (filename: string) => api.restoreBackup(filename),
    onSuccess: () => {
      queryClient.invalidateQueries();
      alert('База данных успешно восстановлена!');
    },
  });

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-brand-indigo" />
          <span>Настройки системы и ИИ</span>
        </h1>
        <p className="text-xs text-slate-400">
          Конфигурация Google Gemini API, локального Ollama, параметров обучения и резервного копирования
        </p>
      </div>

      {/* AI Providers Section */}
      <div className="p-6 rounded-2xl bg-graphite-900 border border-graphite-700/80 space-y-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-graphite-700/60 pb-4">
          <div className="flex items-center gap-3">
            <Cpu className="w-5 h-5 text-brand-indigo" />
            <h2 className="text-base font-bold text-white">Провайдеры искусственного интеллекта</h2>
          </div>

          <div className="flex items-center gap-2 bg-graphite-800 p-1 rounded-xl border border-graphite-700">
            <button
              onClick={() => setActiveProvider('gemini')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeProvider === 'gemini' ? 'bg-brand-indigo text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Google Gemini
            </button>
            <button
              onClick={() => setActiveProvider('ollama')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeProvider === 'ollama' ? 'bg-brand-indigo text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Ollama (Локальный)
            </button>
          </div>
        </div>

        {/* Gemini settings */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Key className="w-4 h-4 text-brand-blue" />
              <span>Google Gemini API</span>
            </h3>
            {settings?.gemini_api_key_configured ? (
              <span className="flex items-center gap-1.5 text-xs text-brand-emerald font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Ключ сохранён</span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs text-amber-400 font-semibold">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Ключ не настроен</span>
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">
                API Ключ Google Gemini:
              </label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder={settings?.gemini_api_key_configured ? '••••••••••••••••••••' : 'AIzaSy...'}
                className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Модель Gemini:</label>
              <select
                value={geminiModel}
                onChange={(e) => setGeminiModel(e.target.value)}
                className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-indigo"
              >
                <option value="gemini-2.5-flash">gemini-2.5-flash (Рекомендуется)</option>
                <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                <option value="gemini-1.5-flash">gemini-1.5-flash</option>
              </select>
            </div>
          </div>
        </div>

        {/* Ollama settings */}
        <div className="space-y-4 pt-4 border-t border-graphite-700/50">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-purple" />
            <span>Локальный сервер Ollama</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Базовый URL Ollama:</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                placeholder="http://127.0.0.1:11434"
                className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-indigo"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Модель Ollama:</label>
              <input
                type="text"
                value={ollamaModel}
                onChange={(e) => setOllamaModel(e.target.value)}
                placeholder="llama3:latest"
                className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-indigo"
              />
            </div>
          </div>
        </div>

        {/* Learning Mode default */}
        <div className="space-y-2 pt-4 border-t border-graphite-700/50">
          <label className="block text-xs text-slate-400">Режим обучения по умолчанию:</label>
          <select
            value={defaultMode}
            onChange={(e) => setDefaultMode(e.target.value)}
            className="w-full sm:w-1/2 bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-indigo"
          >
            <option value="free">Свободное обучение (модель + источники по желанию)</option>
            <option value="my_materials_plus_ai">Мои материалы + знания ИИ (приоритет библиотеки)</option>
            <option value="only_my_materials">Только мои материалы (строгое цитирование)</option>
          </select>
        </div>

        {/* Save and Test Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-graphite-700/60">
          <div className="flex items-center gap-3">
            <button
              onClick={() => updateMutation.mutate()}
              disabled={updateMutation.isPending}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-xs shadow-md transition-all active:scale-95 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{updateMutation.isPending ? 'Сохранение...' : 'Сохранить настройки'}</span>
            </button>

            <button
              onClick={() => testConnectionMutation.mutate()}
              disabled={testConnectionMutation.isPending}
              className="px-4 py-2.5 rounded-xl bg-graphite-800 hover:bg-graphite-700 text-slate-300 hover:text-white border border-graphite-700 text-xs font-semibold transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {testConnectionMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin text-brand-indigo" />
              ) : null}
              <span>Проверить подключение</span>
            </button>
          </div>

          {saveSuccess && (
            <span className="text-xs text-brand-emerald font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Настройки успешно сохранены!</span>
            </span>
          )}
        </div>

        {/* Test Result Message */}
        {testStatus && (
          <div
            className={`p-3.5 rounded-xl border text-xs ${
              testStatus.success
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : 'bg-red-950/40 border-red-800 text-red-300'
            }`}
          >
            <div className="font-bold mb-1">
              {testStatus.success ? '✓ Подключение успешно:' : '✗ Ошибка подключения:'}
            </div>
            <pre className="text-[11px] whitespace-pre-wrap">{JSON.stringify(testStatus, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Database & Backups Section */}
      <div className="p-6 rounded-2xl bg-graphite-900 border border-graphite-700/80 space-y-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-graphite-700/60 pb-4">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-brand-emerald" />
            <h2 className="text-base font-bold text-white">База данных SQLite и Резервное копирование</h2>
          </div>

          <button
            onClick={() => backupMutation.mutate()}
            disabled={backupMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-emerald hover:bg-emerald-600 text-white font-semibold text-xs shadow transition-all disabled:opacity-50"
          >
            {backupMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
            <span>Создать резервную копию</span>
          </button>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Размер базы данных: <strong className="text-white">{formatBytes(settings?.database_size_bytes || 0)}</strong></span>
          <span>Всего резервных копий: <strong className="text-white">{backups.length}</strong></span>
        </div>

        {/* Backups List */}
        <div className="space-y-2">
          {backups.length > 0 ? (
            backups.map((b) => (
              <div
                key={b.filename}
                className="p-3.5 rounded-xl bg-graphite-800/80 border border-graphite-700/50 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-white">{b.filename}</span>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {formatBytes(b.size_bytes)} • {new Date(b.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>

                <button
                  onClick={() => {
                    if (confirm(`Восстановить базу данных из копии «${b.filename}»?`)) {
                      restoreMutation.mutate(b.filename);
                    }
                  }}
                  className="px-3 py-1.5 rounded-lg bg-graphite-700 hover:bg-brand-indigo text-slate-200 hover:text-white font-semibold text-[11px] transition-colors"
                >
                  Восстановить
                </button>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-500 italic">Резервных копий пока нет.</p>
          )}
        </div>
      </div>
    </div>
  );
};
