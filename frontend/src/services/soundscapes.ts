// Web Audio API Generative Study Soundscapes
// 100% reliable, zero external dependencies, no CORS issues, works offline and on mobile.

export type SoundscapeType = 'calm_piano' | 'rain' | 'lofi' | 'nature' | 'deep_focus';

export interface SoundscapeTrack {
  id: SoundscapeType;
  name: string;
  description: string;
  iconName: string;
}

export const SOUNDSCAPE_TRACKS: SoundscapeTrack[] = [
  { id: 'calm_piano', name: 'Calm Piano', description: 'Медитативные фортепианные гармонии', iconName: 'Music' },
  { id: 'rain', name: 'Rain & Ambient', description: 'Успокаивающий шум дождя и атмосфера', iconName: 'CloudRain' },
  { id: 'lofi', name: 'Lo-Fi Study', description: 'Мягкий инструментальный Lo-Fi', iconName: 'Headphones' },
  { id: 'nature', name: 'Nature Sounds', description: 'Звуки леса и спокойного ручья', iconName: 'Trees' },
  { id: 'deep_focus', name: 'Deep Focus (432Hz)', description: 'Бинауральный эмбиент для глубокой концентрации', iconName: 'Zap' },
];

class AudioEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private activeNodes: (AudioNode | number)[] = [];
  private currentTrack: SoundscapeType = 'calm_piano';
  private isPlaying = false;
  private volume = 0.5;
  private timerId: number | null = null;

  private initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.05);
    }
  }

  public getVolume(): number {
    return this.volume;
  }

  public getIsPlaying(): boolean {
    return this.isPlaying;
  }

  public getCurrentTrack(): SoundscapeType {
    return this.currentTrack;
  }

  public stop() {
    if (!this.isPlaying) return;
    this.isPlaying = false;
    if (this.timerId !== null) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
    if (this.masterGain && this.ctx) {
      // Smooth fade out
      this.masterGain.gain.setTargetAtTime(0, this.ctx.currentTime, 0.15);
    }
    setTimeout(() => {
      this.clearActiveNodes();
    }, 200);
  }

  private clearActiveNodes() {
    for (const item of this.activeNodes) {
      if (typeof item === 'number') {
        clearInterval(item);
      } else {
        try {
          (item as any).stop?.();
          item.disconnect();
        } catch (_) {}
      }
    }
    this.activeNodes = [];
  }

  public play(track: SoundscapeType) {
    this.initContext();
    if (!this.ctx || !this.masterGain) return;

    this.stop();
    this.currentTrack = track;
    this.isPlaying = true;

    // Reset volume with smooth fade in
    this.masterGain.gain.setValueAtTime(0.01, this.ctx.currentTime);
    this.masterGain.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.2);

    switch (track) {
      case 'calm_piano':
        this.startCalmPiano();
        break;
      case 'rain':
        this.startRain();
        break;
      case 'lofi':
        this.startLoFi();
        break;
      case 'nature':
        this.startNature();
        break;
      case 'deep_focus':
        this.startDeepFocus();
        break;
    }
  }

  // 1. Calm Piano: Pentatonic ambient chord chimes
  private startCalmPiano() {
    if (!this.ctx || !this.masterGain) return;
    const notes = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33, 659.25]; // C major pentatonic
    const playNote = () => {
      if (!this.isPlaying || !this.ctx || !this.masterGain) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      const freq = notes[Math.floor(Math.random() * notes.length)];
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.25, this.ctx.currentTime + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 3.2);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start();
      osc.stop(this.ctx.currentTime + 3.3);
    };

    playNote();
    const id = window.setInterval(() => {
      playNote();
      if (Math.random() > 0.4) {
        setTimeout(playNote, 400);
      }
    }, 2200);
    this.activeNodes.push(id);
  }

  // 2. Rain & Ambient: Filtered pink noise with modulated resonance
  private startRain() {
    if (!this.ctx || !this.masterGain) return;
    const bufferSize = this.ctx.sampleRate * 2;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.04;
      b6 = white * 0.115926;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;
    noise.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(750, this.ctx.currentTime);

    noise.connect(filter);
    filter.connect(this.masterGain);
    noise.start();
    this.activeNodes.push(noise);
  }

  // 3. Lo-Fi Study: Warm electric piano chords
  private startLoFi() {
    if (!this.ctx || !this.masterGain) return;
    const chords = [
      [220.0, 261.63, 329.63, 392.0], // Am7
      [174.61, 220.0, 261.63, 329.63], // Fmaj7
      [196.0, 246.94, 293.66, 349.23], // G7
      [164.81, 196.0, 246.94, 329.63], // Em7
    ];
    let chordIdx = 0;

    const playChord = () => {
      if (!this.isPlaying || !this.ctx || !this.masterGain) return;
      const current = chords[chordIdx % chords.length];
      chordIdx++;

      current.forEach((freq) => {
        if (!this.ctx || !this.masterGain) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const filter = this.ctx.createBiquadFilter();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(600, this.ctx.currentTime);

        gain.gain.setValueAtTime(0, this.ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.12, this.ctx.currentTime + 0.15);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 2.8);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.masterGain);

        osc.start();
        osc.stop(this.ctx.currentTime + 3.0);
      });
    };

    playChord();
    const id = window.setInterval(playChord, 3000);
    this.activeNodes.push(id);
  }

  // 4. Nature Sounds: Gentle stream + subtle chirps
  private startNature() {
    this.startRain(); // Stream bed
    if (!this.ctx || !this.masterGain) return;

    // Random gentle bird chirps
    const chirp = () => {
      if (!this.isPlaying || !this.ctx || !this.masterGain) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const now = this.ctx.currentTime;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(2400 + Math.random() * 800, now);
      osc.frequency.exponentialRampToValueAtTime(1800 + Math.random() * 400, now + 0.15);

      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.06, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(now);
      osc.stop(now + 0.2);
    };

    const id = window.setInterval(() => {
      if (Math.random() > 0.4) {
        chirp();
      }
    }, 3500);
    this.activeNodes.push(id);
  }

  // 5. Deep Focus: 432 Hz binaural ambient drone
  private startDeepFocus() {
    if (!this.ctx || !this.masterGain) return;
    const oscLeft = this.ctx.createOscillator();
    const oscRight = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    oscLeft.type = 'sine';
    oscLeft.frequency.setValueAtTime(216.0, this.ctx.currentTime); // 432 / 2

    oscRight.type = 'sine';
    oscRight.frequency.setValueAtTime(222.0, this.ctx.currentTime); // 6 Hz alpha wave binaural beat

    gain.gain.setValueAtTime(0.18, this.ctx.currentTime);

    oscLeft.connect(gain);
    oscRight.connect(gain);
    gain.connect(this.masterGain);

    oscLeft.start();
    oscRight.start();

    this.activeNodes.push(oscLeft, oscRight);
  }
}

export const audioEngine = new AudioEngine();
