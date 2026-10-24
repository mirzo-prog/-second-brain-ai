import React, { createContext, useContext, useState, useEffect } from 'react';
import { audioEngine, SoundscapeType, SOUNDSCAPE_TRACKS, SoundscapeTrack } from '../services/soundscapes';

interface MusicContextType {
  isPlaying: boolean;
  currentTrack: SoundscapeType;
  volume: number;
  playTrack: (track: SoundscapeType) => void;
  togglePlay: () => void;
  setVolume: (vol: number) => void;
  tracks: SoundscapeTrack[];
  isExpanded: boolean;
  setIsExpanded: (expanded: boolean) => void;
}

const MusicContext = createContext<MusicContextType | null>(null);

export const MusicProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<SoundscapeType>('calm_piano');
  const [volume, setVolumeState] = useState(0.4);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Initial volume
    audioEngine.setVolume(volume);
  }, []);

  const playTrack = (track: SoundscapeType) => {
    setCurrentTrack(track);
    audioEngine.play(track);
    setIsPlaying(true);
  };

  const togglePlay = () => {
    if (isPlaying) {
      audioEngine.stop();
      setIsPlaying(false);
    } else {
      audioEngine.play(currentTrack);
      setIsPlaying(true);
    }
  };

  const handleSetVolume = (vol: number) => {
    const clamped = Math.max(0, Math.min(1, vol));
    setVolumeState(clamped);
    audioEngine.setVolume(clamped);
  };

  return (
    <MusicContext.Provider
      value={{
        isPlaying,
        currentTrack,
        volume,
        playTrack,
        togglePlay,
        setVolume: handleSetVolume,
        tracks: SOUNDSCAPE_TRACKS,
        isExpanded,
        setIsExpanded,
      }}
    >
      {children}
    </MusicContext.Provider>
  );
};

export const useMusic = () => {
  const context = useContext(MusicContext);
  if (!context) {
    throw new Error('useMusic must be used within a MusicProvider');
  }
  return context;
};
