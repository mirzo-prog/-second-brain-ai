import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, DocumentItem } from '../api/client';
import {
  Library,
  Upload,
  Search,
  FileText,
  Trash2,
  Paperclip,
  CheckCircle2,
  FileCode,
  File,
  Loader2,
  Sparkles,
} from 'lucide-react';

export const LibraryPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error('Выберите файл');
      return api.uploadDocument(selectedFile, uploadTitle);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setSelectedFile(null);
      setUploadTitle('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await fetch(`/api/documents/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-400" />;
      case 'docx':
        return <FileText className="w-5 h-5 text-blue-400" />;
      case 'cpp':
      case 'py':
      case 'sh':
        return <FileCode className="w-5 h-5 text-emerald-400" />;
      default:
        return <File className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Библиотека учебных материалов</h1>
          <p className="text-xs text-slate-400">
            PDF, DOCX, Markdown, C++, Python и конспекты с индексацией FTS5 и цитированием
          </p>
        </div>
      </div>

      {/* Upload Box */}
      <div className="p-6 rounded-2xl bg-graphite-900/90 border border-graphite-700/80 shadow-md space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Upload className="w-4 h-4 text-brand-indigo" />
          <span>Загрузка нового учебного материала</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="block text-xs text-slate-400 mb-1">Файл документа:</label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-indigo file:text-white hover:file:bg-indigo-600 file:cursor-pointer"
            />
          </div>

          <div className="md:col-span-1">
            <label className="block text-xs text-slate-400 mb-1">Понятное название (опционально):</label>
            <input
              type="text"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Например: Учебник C++ (Лафоре)"
              className="w-full bg-graphite-800 border border-graphite-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
            />
          </div>

          <div className="md:col-span-1 flex items-end">
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!selectedFile || uploadMutation.isPending}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-blue-600 hover:to-indigo-600 text-white font-semibold text-xs shadow-md disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Индексация документа...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Загрузить и проиндексировать</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* RAG Search Tester */}
      <div className="p-6 rounded-2xl bg-graphite-900/60 border border-graphite-700/60 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Search className="w-4 h-4 text-brand-purple" />
          <span>Семантический и FTS5 поиск по всей библиотеке</span>
        </h3>

        <div className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Введите поисковый запрос (например: «указатели», «права доступа chmod», «виртуальные функции»)..."
            className="flex-1 bg-graphite-800 border border-graphite-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo"
          />
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim() || isSearching}
            className="px-5 py-2.5 rounded-xl bg-graphite-800 hover:bg-brand-indigo text-slate-200 hover:text-white font-semibold text-xs transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>Искать</span>
          </button>
        </div>

        {/* Search Results Display */}
        {searchResults.length > 0 && (
          <div className="space-y-3 pt-3">
            <h4 className="text-xs font-semibold text-indigo-300">
              Найдено фрагментов: {searchResults.length}
            </h4>
            <div className="space-y-2">
              {searchResults.map((res, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-graphite-800/80 border border-graphite-700/60 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-bold text-white">
                      «{res.doc_title}» {res.page ? `• стр. ${res.page}` : ''} {res.section ? `• ${res.section}` : ''}
                    </span>
                    <span className="text-indigo-400 font-mono">BM25: {res.score?.toFixed(2)}</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{res.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Library className="w-5 h-5 text-brand-indigo" />
          <span>Загруженные документы ({documents.length})</span>
        </h2>

        {isLoading ? (
          <div className="flex justify-center p-8">
            <Loader2 className="w-6 h-6 animate-spin text-brand-indigo" />
          </div>
        ) : documents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-5 rounded-xl bg-graphite-900 border border-graphite-700/60 flex items-start justify-between gap-4"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="p-2.5 rounded-lg bg-graphite-800 shrink-0">
                    {getFileIcon(doc.file_type)}
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-semibold text-sm text-white truncate">{doc.title}</h4>
                    <p className="text-xs text-slate-400 truncate mt-0.5">{doc.filename}</p>
                    <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{doc.chunks_count} фрагментов</span>
                      <span>•</span>
                      <span className="text-brand-emerald flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>FTS5 индекс</span>
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => {
                    if (confirm(`Удалить документ «${doc.title}» и его поисковый индекс?`)) {
                      deleteMutation.mutate(doc.id);
                    }
                  }}
                  className="text-slate-500 hover:text-red-400 transition-colors p-1"
                  title="Удалить документ"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-xl bg-graphite-900/40 border border-dashed border-graphite-700 text-center text-slate-400 text-xs">
            В библиотеке пока нет документов. Загрузите учебник в формате PDF, DOCX или конспект в Markdown выше!
          </div>
        )}
      </div>
    </div>
  );
};
