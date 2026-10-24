import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  Download,
  BookOpen,
  Code,
  Image as ImageIcon,
  Sparkles,
} from 'lucide-react';

export interface SlideData {
  title: string;
  subtitle?: string;
  bullets?: string[];
  code?: string;
  language?: string;
  image_url?: string;
  image_caption?: string;
  key_takeaway?: string;
  formula?: string;
}

interface PresentationViewerProps {
  lessonTitle: string;
  courseTitle?: string;
  slidesJson?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const PresentationViewer: React.FC<PresentationViewerProps> = ({
  lessonTitle,
  courseTitle,
  slidesJson,
  isOpen,
  onClose,
}) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Parse slides
  let slides: SlideData[] = [];
  try {
    if (slidesJson) {
      slides = JSON.parse(slidesJson);
    }
  } catch (e) {
    slides = [];
  }

  // Fallback slides if empty or parse failed
  if (!slides || slides.length === 0) {
    slides = [
      {
        title: lessonTitle,
        subtitle: courseTitle || 'Интерактивный учебный курс',
        bullets: [
          'Фундаментальные концепции и принципы темы',
          'Практическое применение и разбор типовых задач',
          'Проверка знаний и закрепление материала',
        ],
        key_takeaway: 'Интерактивная презентация подготовлена ИИ Second Brain AI.',
      },
    ];
  }

  const totalSlides = slides.length;
  const currentSlide = slides[currentSlideIndex] || slides[0];

  const nextSlide = useCallback(() => {
    setCurrentSlideIndex((prev) => (prev < totalSlides - 1 ? prev + 1 : prev));
  }, [totalSlides]);

  const prevSlide = useCallback(() => {
    setCurrentSlideIndex((prev) => (prev > 0 ? prev - 1 : prev));
  }, []);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'Backspace') {
        e.preventDefault();
        prevSlide();
      } else if (e.key === 'Escape') {
        if (document.fullscreenElement) {
          document.exitFullscreen().catch(() => {});
        } else {
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, nextSlide, prevSlide, onClose]);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // PDF export / Print action
  const handlePrint = () => {
    window.print();
  };

  if (!isOpen) return null;

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 bg-dark-950 text-white flex flex-col justify-between overflow-hidden select-none print:bg-white print:text-black print:overflow-visible"
    >
      {/* Top Bar (hidden in print) */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-dark-800 bg-dark-900/80 backdrop-blur print:hidden">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary-500/10 text-primary-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-dark-100">{lessonTitle}</h3>
            {courseTitle && <p className="text-xs text-dark-400">{courseTitle}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-800 hover:bg-dark-700 text-xs text-dark-200 hover:text-white transition"
            title="Печать / Сохранить в PDF"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">PDF / Печать</span>
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-dark-300 hover:text-white transition"
            title={isFullscreen ? 'Выйти из полноэкранного режима' : 'На весь экран'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-dark-300 hover:text-white transition ml-2"
            title="Закрыть презентацию (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Slide Stage */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 overflow-y-auto">
        <div className="max-w-4xl w-full bg-gradient-to-b from-dark-900 to-dark-950 border border-dark-800/80 rounded-3xl p-8 sm:p-12 shadow-2xl relative min-h-[460px] flex flex-col justify-between">
          <div>
            {/* Header / Subtitle */}
            {currentSlide.subtitle && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/10 text-primary-400 text-xs font-medium mb-3">
                <Sparkles className="w-3 h-3" />
                {currentSlide.subtitle}
              </div>
            )}

            {/* Slide Title */}
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-6">
              {currentSlide.title}
            </h2>

            {/* Content grid */}
            <div className={`grid gap-6 ${currentSlide.image_url || currentSlide.code ? 'md:grid-cols-2' : 'grid-cols-1'}`}>
              {/* Bullet Points */}
              {currentSlide.bullets && currentSlide.bullets.length > 0 && (
                <ul className="space-y-3.5">
                  {currentSlide.bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-dark-200 text-sm sm:text-base leading-relaxed">
                      <span className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-primary-400" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              )}

              {/* Media Block: Image or Code */}
              {currentSlide.image_url && (
                <div className="rounded-2xl overflow-hidden border border-dark-700/60 bg-dark-900 flex flex-col">
                  <div className="relative h-48 sm:h-56 bg-dark-950 flex items-center justify-center p-2">
                    <img
                      src={currentSlide.image_url}
                      alt={currentSlide.image_caption || 'Иллюстрация к слайду'}
                      className="max-h-full max-w-full object-contain rounded-lg"
                      loading="lazy"
                    />
                  </div>
                  {currentSlide.image_caption && (
                    <div className="p-2.5 bg-dark-850 text-[11px] text-dark-400 flex items-center gap-1.5 border-t border-dark-800">
                      <ImageIcon className="w-3.5 h-3.5 flex-shrink-0 text-primary-400" />
                      <span className="truncate">{currentSlide.image_caption}</span>
                    </div>
                  )}
                </div>
              )}

              {currentSlide.code && (
                <div className="rounded-2xl overflow-hidden border border-dark-700/60 bg-dark-900 flex flex-col">
                  <div className="px-3 py-1.5 bg-dark-850 text-[11px] text-dark-400 flex items-center gap-1.5 border-b border-dark-800">
                    <Code className="w-3.5 h-3.5 text-primary-400" />
                    <span>{currentSlide.language || 'code'}</span>
                  </div>
                  <pre className="p-4 text-xs font-mono text-dark-200 overflow-x-auto leading-relaxed max-h-52">
                    <code>{currentSlide.code}</code>
                  </pre>
                </div>
              )}
            </div>
          </div>

          {/* Key Takeaway Banner */}
          {currentSlide.key_takeaway && (
            <div className="mt-8 p-4 rounded-2xl bg-primary-500/10 border border-primary-500/20 text-xs sm:text-sm text-primary-200 flex items-center gap-3">
              <span className="font-semibold text-primary-400 flex-shrink-0">Главный вывод:</span>
              <p className="line-clamp-2">{currentSlide.key_takeaway}</p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Bar: Navigation and Progress (hidden in print) */}
      <div className="px-6 py-4 border-t border-dark-800 bg-dark-900/80 backdrop-blur print:hidden flex flex-col gap-3">
        {/* Progress Bar */}
        <div className="w-full bg-dark-800 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-primary-500 h-full transition-all duration-300 ease-out"
            style={{ width: `${((currentSlideIndex + 1) / totalSlides) * 100}%` }}
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="text-xs text-dark-400 font-medium">
            Слайд <span className="text-white font-semibold">{currentSlideIndex + 1}</span> из{' '}
            <span className="text-white font-semibold">{totalSlides}</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={prevSlide}
              disabled={currentSlideIndex === 0}
              className={`p-2 rounded-xl border border-dark-700 transition ${
                currentSlideIndex === 0
                  ? 'opacity-40 cursor-not-allowed text-dark-500'
                  : 'hover:bg-dark-800 text-white'
              }`}
              title="Предыдущий слайд (←)"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <button
              onClick={nextSlide}
              disabled={currentSlideIndex === totalSlides - 1}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-xs transition ${
                currentSlideIndex === totalSlides - 1
                  ? 'opacity-40 cursor-not-allowed bg-dark-800 text-dark-400'
                  : 'bg-primary-500 hover:bg-primary-600 text-white shadow-md shadow-primary-500/20'
              }`}
              title="Следующий слайд (→ или Пробел)"
            >
              <span>Далее</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
