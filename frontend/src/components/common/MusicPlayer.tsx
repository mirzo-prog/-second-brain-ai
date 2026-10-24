import React from 'react';
import { useMusic } from '../../context/MusicContext';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Music,
  CloudRain,
  Headphones,
  Trees,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const trackIcons: Record<string, React.ReactNode> = {
  calm_piano: <Music className="w-4 h-4 text-primary-400" />,
  rain: <CloudRain className="w-4 h-4 text-cyan-400" />,
  lofi: <Headphones className="w-4 h-4 text-emerald-400" />,
  nature: <Trees className="w-4 h-4 text-green-400" />,
  deep_focus: <Zap className="w-4 h-4 text-purple-400" />,
};

export const MusicPlayer: React.FC = () => {
  const {
    isPlaying,
    currentTrack,
    volume,
    playTrack,
    togglePlay,
    setVolume,
    tracks,
    isExpanded,
    setIsExpanded,
  } = useMusic();

  const currentTrackData = tracks.find((t) => t.id === currentTrack) || tracks[0];

  return (
    <div className="fixed bottom-5 right-5 z-40 select-none">
      {/* Expanded Modal / Card */}
      {isExpanded && (
        <div className="mb-3 w-80 rounded-2xl bg-dark-800/95 backdrop-blur-xl border border-dark-600 shadow-2xl p-4 text-dark-100 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-dark-700">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-primary-500/10 text-primary-400">
                <Music className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Фоновая музыка</h4>
                <p className="text-xs text-dark-400">Концентрация и обучение</p>
              </div>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1 rounded-lg text-dark-400 hover:text-white hover:bg-dark-700 transition"
              title="Свернуть"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>

          {/* Track selection */}
          <div className="my-3 space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {tracks.map((track) => {
              const active = currentTrack === track.id;
              return (
                <button
                  key={track.id}
                  onClick={() => playTrack(track.id)}
                  className={`w-full flex items-center gap-2.5 p-2 rounded-xl text-left transition ${
                    active
                      ? 'bg-primary-500/15 border border-primary-500/30 text-white'
                      : 'hover:bg-dark-700/60 text-dark-300 hover:text-white border border-transparent'
                  }`}
                >
                  <div className="p-1.5 rounded-lg bg-dark-700/80">
                    {trackIcons[track.id]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium truncate">{track.name}</span>
                      {active && isPlaying && (
                        <span className="flex gap-0.5 items-end h-3">
                          <span className="w-0.5 h-3 bg-primary-400 animate-pulse rounded" />
                          <span className="w-0.5 h-2 bg-primary-400 animate-pulse rounded delay-75" />
                          <span className="w-0.5 h-2.5 bg-primary-400 animate-pulse rounded delay-150" />
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-dark-400 truncate block">
                      {track.description}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Volume Control */}
          <div className="pt-3 border-t border-dark-700 flex items-center gap-3">
            <button
              onClick={() => setVolume(volume > 0 ? 0 : 0.4)}
              className="text-dark-400 hover:text-white transition"
              title={volume === 0 ? 'Включить звук' : 'Отключить звук'}
            >
              {volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="flex-1 h-1.5 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
            <span className="text-xs text-dark-400 w-8 text-right">
              {Math.round(volume * 100)}%
            </span>
          </div>
        </div>
      )}

      {/* Mini Floating Pill */}
      <div className="flex items-center gap-2 p-1.5 pl-3 rounded-full bg-dark-800/90 backdrop-blur-md border border-dark-600/80 shadow-lg hover:border-primary-500/40 transition">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 hover:opacity-80 transition"
        >
          {isPlaying ? (
            <span className="flex gap-0.5 items-end h-3.5 mr-0.5">
              <span className="w-0.5 h-3.5 bg-primary-400 animate-bounce rounded" />
              <span className="w-0.5 h-2 bg-primary-400 animate-bounce rounded delay-100" />
              <span className="w-0.5 h-3 bg-primary-400 animate-bounce rounded delay-200" />
            </span>
          ) : (
            trackIcons[currentTrack]
          )}
          <span className="text-xs font-medium text-dark-200 max-w-[110px] truncate">
            {currentTrackData.name}
          </span>
        </button>

        <button
          onClick={togglePlay}
          className={`p-2 rounded-full transition ${
            isPlaying
              ? 'bg-primary-500 text-white shadow-md shadow-primary-500/30'
              : 'bg-dark-700 text-dark-300 hover:text-white hover:bg-dark-600'
          }`}
          title={isPlaying ? 'Пауза' : 'Воспроизведение'}
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
        </button>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1.5 rounded-full text-dark-400 hover:text-white hover:bg-dark-700 transition"
          title={isExpanded ? 'Свернуть' : 'Выбрать трек и громкость'}
        >
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
};
