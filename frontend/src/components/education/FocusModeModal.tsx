import React, { useState, useEffect } from 'react';
import {
  X,
  Play,
  Pause,
  RotateCcw,
  Type,
  Maximize,
  Minimize,
  Music,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useMusic } from '../../context/MusicContext';

interface FocusModeModalProps {
  lessonTitle: string;
  courseTitle?: string;
  contentMarkdown?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const FocusModeModal: React.FC<FocusModeModalProps> = ({
  lessonTitle,
  courseTitle,
  contentMarkdown,
  isOpen,
  onClose,
}) => {
  // Pomodoro timer state
  const [timerMinutes, setTimerMinutes] = useState(25);
  const [secondsRemaining, setSecondsRemaining] = useState(25 * 60);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  // Font size control
  const [fontSize, setFontSize] = useState<'normal' | 'large' | 'xlarge'>('large');

  // Music context
  const { isPlaying, togglePlay, currentTrack, tracks, playTrack } = useMusic();

  // Fullscreen
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Change duration preset
  const selectDuration = (mins: number) => {
    setIsTimerRunning(false);
    setTimerMinutes(mins);
    setSecondsRemaining(mins * 60);
  };

  // Timer tick
  useEffect(() => {
    let interval: any = null;
    if (isTimerRunning && secondsRemaining > 0) {
      interval = setInterval(() => {
        setSecondsRemaining((prev) => prev - 1);
      }, 1000);
    } else if (secondsRemaining === 0 && isTimerRunning) {
      setIsTimerRunning(false);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, secondsRemaining]);

  const toggleTimer = () => {
    setIsTimerRunning(!isTimerRunning);
  };

  const resetTimer = () => {
    setIsTimerRunning(false);
    setSecondsRemaining(timerMinutes * 60);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  if (!isOpen) return null;

  const fontClass =
    fontSize === 'normal'
      ? 'text-base leading-relaxed'
      : fontSize === 'large'
      ? 'text-lg leading-loose'
      : 'text-xl leading-loose';

  const currentTrackData = tracks.find((t) => t.id === currentTrack) || tracks[0];

  return (
    <div className="fixed inset-0 z-50 bg-dark-950 text-dark-100 flex flex-col justify-between overflow-hidden select-none animate-in fade-in duration-200">
      {/* Top Distraction-free Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-dark-800/80 bg-dark-900/60 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary-500/10 text-primary-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full">
                Режим фокуса
              </span>
              {courseTitle && <span className="text-xs text-dark-400">• {courseTitle}</span>}
            </div>
            <h2 className="text-sm sm:text-base font-bold text-white truncate max-w-md">
              {lessonTitle}
            </h2>
          </div>
        </div>

        {/* Center: Pomodoro Widget */}
        <div className="flex items-center gap-3 bg-dark-850 border border-dark-750 px-4 py-1.5 rounded-2xl shadow-inner">
          <Clock className="w-4 h-4 text-primary-400" />
          <span className="text-lg font-mono font-bold text-white tracking-widest">
            {formatTime(secondsRemaining)}
          </span>

          <div className="flex items-center gap-1">
            <button
              onClick={toggleTimer}
              className="p-1 rounded-lg bg-dark-700 hover:bg-dark-600 text-white transition"
              title={isTimerRunning ? 'Пауза' : 'Старт таймера'}
            >
              {isTimerRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={resetTimer}
              className="p-1 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition"
              title="Сброс таймера"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-1 border-l border-dark-700 pl-2">
            {[25, 45, 60].map((m) => (
              <button
                key={m}
                onClick={() => selectDuration(m)}
                className={`text-[11px] px-2 py-0.5 rounded-md font-medium transition ${
                  timerMinutes === m
                    ? 'bg-primary-500/20 text-primary-300 font-bold'
                    : 'text-dark-400 hover:text-white'
                }`}
              >
                {m}м
              </button>
            ))}
          </div>
        </div>

        {/* Right Tools: Font size, Music toggle, Fullscreen, Close */}
        <div className="flex items-center gap-2">
          {/* Quick Music Toggle */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-dark-850 border border-dark-750 text-xs">
            <button
              onClick={togglePlay}
              className="flex items-center gap-1.5 text-dark-300 hover:text-white transition"
              title={isPlaying ? 'Остановить музыку' : 'Включить фоновую музыку'}
            >
              <Music className={`w-3.5 h-3.5 ${isPlaying ? 'text-primary-400 animate-spin' : ''}`} />
              <span className="truncate max-w-[90px]">{currentTrackData.name}</span>
            </button>
          </div>

          {/* Font size switcher */}
          <div className="flex items-center bg-dark-850 border border-dark-750 rounded-xl p-0.5">
            <button
              onClick={() => setFontSize('normal')}
              className={`p-1.5 rounded-lg text-xs ${
                fontSize === 'normal' ? 'bg-primary-500 text-white font-bold' : 'text-dark-400'
              }`}
              title="Стандартный шрифт"
            >
              A
            </button>
            <button
              onClick={() => setFontSize('large')}
              className={`p-1.5 rounded-lg text-sm ${
                fontSize === 'large' ? 'bg-primary-500 text-white font-bold' : 'text-dark-400'
              }`}
              title="Крупный шрифт"
            >
              A+
            </button>
            <button
              onClick={() => setFontSize('xlarge')}
              className={`p-1.5 rounded-lg text-base font-bold ${
                fontSize === 'xlarge' ? 'bg-primary-500 text-white' : 'text-dark-400'
              }`}
              title="Максимальный шрифт"
            >
              A++
            </button>
          </div>

          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-xl bg-dark-850 hover:bg-dark-750 text-dark-400 hover:text-white transition"
            title="Полноэкранный режим"
          >
            {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-dark-850 hover:bg-dark-750 text-dark-400 hover:text-white transition"
            title="Выйти из режима фокуса"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Distraction-free Reading Content */}
      <div className="flex-1 overflow-y-auto px-6 py-12 flex justify-center">
        <div className="max-w-3xl w-full">
          <div className={`prose prose-invert prose-emerald max-w-none ${fontClass} text-dark-200 select-text`}>
            {contentMarkdown ? (
              <div className="space-y-4 whitespace-pre-wrap font-sans leading-relaxed">
                {contentMarkdown}
              </div>
            ) : (
              <p className="text-dark-400">Содержимое урока загружается...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
