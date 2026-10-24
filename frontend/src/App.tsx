import React from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { DashboardPage } from './pages/DashboardPage';
import { CoursesPage } from './pages/CoursesPage';
import { CourseDetailPage } from './pages/CourseDetailPage';
import { LessonViewPage } from './pages/LessonViewPage';
import { TutorPage } from './pages/TutorPage';
import { LibraryPage } from './pages/LibraryPage';
import { KnowledgeMapPage } from './pages/KnowledgeMapPage';
import { PracticePage } from './pages/PracticePage';
import { SkillsPage } from './pages/SkillsPage';
import { StatisticsPage } from './pages/StatisticsPage';
import { StudyPlanPage } from './pages/StudyPlanPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

const LayoutContent: React.FC = () => {
  const location = useLocation();

  const getPageTitle = (pathname: string) => {
    if (pathname === '/') return { title: 'Главная панель', subtitle: 'Обзор вашего прогресса и активные темы' };
    if (pathname.startsWith('/courses/')) return { title: 'Учебный курс', subtitle: 'Дорожная карта и уроки' };
    if (pathname === '/courses') return { title: 'Мои курсы', subtitle: 'Каталог ваших учебных программ' };
    if (pathname === '/tutor') return { title: 'ИИ-преподаватель', subtitle: 'Интерактивные занятия и консультации' };
    if (pathname === '/library') return { title: 'Библиотека материалов', subtitle: 'PDF, DOCX, код и конспекты с RAG' };
    if (pathname === '/knowledge-map') return { title: 'Карта знаний', subtitle: 'Визуальный граф навыков и зависимостей' };
    if (pathname === '/practice') return { title: 'Практика и Песочница', subtitle: 'Выполнение кода и тестирование' };
    if (pathname === '/skills') return { title: 'Мои навыки', subtitle: 'Отслеживание подтверждённых навыков' };
    if (pathname === '/statistics') return { title: 'Статистика', subtitle: 'Аналитика времени и продуктивности' };
    if (pathname === '/study-plan') return { title: 'План обучения', subtitle: 'Интервальные повторения SM-2' };
    if (pathname === '/settings') return { title: 'Настройки', subtitle: 'Конфигурация Gemini, Ollama и резервных копий' };
    return { title: 'Second Brain AI', subtitle: 'Интеллектуальная система обучения' };
  };

  const { title, subtitle } = getPageTitle(location.pathname);

  return (
    <div className="flex min-h-screen bg-graphite-950 text-slate-100 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={title} subtitle={subtitle} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/courses/:id" element={<CourseDetailPage />} />
            <Route path="/courses/:courseId/lessons/:lessonId" element={<LessonViewPage />} />
            <Route path="/tutor" element={<TutorPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/knowledge-map" element={<KnowledgeMapPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/skills" element={<SkillsPage />} />
            <Route path="/statistics" element={<StatisticsPage />} />
            <Route path="/study-plan" element={<StudyPlanPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LayoutContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
