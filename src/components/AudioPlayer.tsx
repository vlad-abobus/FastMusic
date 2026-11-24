import React, { useState, useEffect, useRef } from "react";
import { 
  Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, 
  Disc, Sliders, Radio, Music2, Share2, ClipboardCheck
} from "lucide-react";
import { PlaybackItem } from "../types";

interface AudioPlayerProps {
  currentTrack: PlaybackItem | null;
  isPlaying: boolean;
  onPlayPauseToggle: (playing: boolean) => void;
  onNext: () => void;
  onPrev: () => void;
}

export default function AudioPlayer({
  currentTrack,
  isPlaying,
  onPlayPauseToggle,
  onNext,
  onPrev
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [duration, setDuration] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [volume, setVolumeState] = useState<number>(0.5);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Synchronize audio source and state
  useEffect(() => {
    if (!audioRef.current) return;

    if (currentTrack) {
      const wasPlaying = isPlaying;
      audioRef.current.src = currentTrack.url;
      audioRef.current.load();

      if (wasPlaying) {
        audioRef.current.play()
          .then(() => onPlayPauseToggle(true))
          .catch((err) => {
            console.error("Autoplay failed:", err);
            onPlayPauseToggle(false);
          });
      } else {
        // Simple manual trigger
        audioRef.current.play()
          .then(() => onPlayPauseToggle(true))
          .catch(() => onPlayPauseToggle(false));
      }
    } else {
      audioRef.current.pause();
      onPlayPauseToggle(false);
      setCurrentTime(0);
      setDuration(0);
    }
  }, [currentTrack]);

  // Synchronize play/pause state
  useEffect(() => {
    if (!audioRef.current || !currentTrack) return;

    if (isPlaying) {
      audioRef.current.play().catch(() => onPlayPauseToggle(false));
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying]);

  // Handle basic volume setup
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseFloat(e.target.value);
    setVolumeState(v);
    setIsMuted(v === 0);
    if (audioRef.current) {
      audioRef.current.volume = v;
      audioRef.current.muted = v === 0;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    audioRef.current.muted = nextMute;
    if (!nextMute && volume === 0) {
      setVolumeState(0.3);
      audioRef.current.volume = 0.3;
    }
  };

  // Time ticks & Range adjustments
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current || currentTrack?.isRadio) return;
    const time = parseFloat(e.target.value);
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const onTimeUpdate = () => {
    if (!audioRef.current) return;
    setCurrentTime(audioRef.current.currentTime);
  };

  const onLoadedMetadata = () => {
    if (!audioRef.current) return;
    // Set duration
    setDuration(audioRef.current.duration || 30);
  };

  const onEnded = () => {
    onNext();
  };

  const copyShareLink = () => {
    if (!currentTrack) return;
    const text = `${currentTrack.artist} - ${currentTrack.title} (FastMusic: ${currentTrack.isRadio ? 'Радио' : 'Музыка'})`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const formatTime = (time: number) => {
    if (isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div id="persistent-player-card" className="bg-[#050505]/95 border-t border-white/10 p-4 sticky bottom-0 z-50 shadow-2xl backdrop-blur-md">
      <audio
        ref={audioRef}
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMetadata}
        onEnded={onEnded}
      />

      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Track Info */}
        <div className="flex items-center gap-3 w-full md:w-1/4 min-w-[200px]">
          <div className="relative group w-14 h-14 bg-zinc-950 rounded-lg overflow-hidden flex-shrink-0 border border-white/10 shadow-md">
            {currentTrack?.album_art ? (
              <img 
                src={currentTrack.album_art} 
                alt={currentTrack.title}
                referrerPolicy="no-referrer"
                className={`w-full h-full object-cover transition-transform duration-700 ${isPlaying ? 'animate-[spin_10s_linear_infinite]' : ''}`}
                id="player-album-art"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white/30">
                <Music2 className="w-6 h-6 animate-pulse" />
              </div>
            )}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
              {currentTrack?.isRadio ? <Radio className="w-4 h-4 text-amber-500" /> : <Music2 className="w-4 h-4 text-amber-500" />}
            </div>
          </div>
          <div className="overflow-hidden flex-1 select-none">
            <h4 className="text-zinc-150 font-medium text-sm truncate animate-fade-in" id="current-track-title">
              {currentTrack ? currentTrack.title : "Выберите песню..."}
            </h4>
            <p className="text-white/40 text-xs truncate" id="current-track-artist">
              {currentTrack ? currentTrack.artist : "Или включите Радио"}
            </p>
            {currentTrack && (
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded tracking-wider uppercase ${currentTrack.isRadio ? 'bg-amber-500/10 text-amber-550 border border-amber-500/20' : 'bg-amber-600/10 text-amber-500 border border-amber-600/20'}`}>
                  {currentTrack.isRadio ? "РАДИО" : currentTrack.localId ? "MP3 ЛОКАЛЬНЫЙ" : "ПОТОКОВЫЙ"}
                </span>
                
                <button 
                  onClick={copyShareLink} 
                  title="Поделиться треком" 
                  className="p-1 hover:text-white text-white/40 rounded transition-colors"
                >
                  {copied ? <ClipboardCheck className="w-3 h-3 text-amber-500" /> : <Share2 className="w-3 h-3" />}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Player Controls & Progress bar */}
        <div className="flex flex-col items-center gap-2 w-full md:w-2/4">
          <div className="flex items-center gap-6">
            <button 
              onClick={onPrev}
              disabled={!currentTrack || currentTrack.isRadio}
              className="text-white/40 hover:text-white active:scale-95 disabled:opacity-10 disabled:cursor-not-allowed transition-all"
              id="player-prev-btn"
            >
              <SkipBack className="w-5 h-5 fill-current" />
            </button>
            <button
              onClick={() => onPlayPauseToggle(!isPlaying)}
              disabled={!currentTrack}
              className="w-10 h-10 rounded-full bg-amber-600 hover:bg-amber-505 text-white flex items-center justify-center shadow-lg hover:shadow-amber-500/20 active:scale-90 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed transition-all"
              id="player-play-pause-btn"
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
            </button>
            <button 
              onClick={onNext}
              disabled={!currentTrack || currentTrack.isRadio}
              className="text-white/40 hover:text-white active:scale-95 disabled:opacity-10 disabled:cursor-not-allowed transition-all"
              id="player-next-btn"
            >
              <SkipForward className="w-5 h-5 fill-current" />
            </button>
          </div>

          <div className="flex items-center gap-3 w-full px-2 select-none">
            <span className="text-[11px] font-mono text-white/30 w-10 text-right">
              {currentTrack?.isRadio ? "0:00" : formatTime(currentTime)}
            </span>
            <div className="relative flex-1 group">
              <input 
                type="range"
                min="0"
                max={duration || 30}
                value={currentTrack?.isRadio ? 0 : currentTime}
                onChange={handleSeek}
                disabled={!currentTrack || currentTrack.isRadio}
                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-amber-550 group-hover:h-1.5 transition-all outline-none disabled:cursor-not-allowed"
                style={{
                  background: `linear-gradient(to right, #d97706 0%, #d97706 ${progressPercent}%, rgba(255,255,255,0.1) ${progressPercent}%, rgba(255,255,255,0.1) 100%)`
                }}
              />
            </div>
            <span className="text-[11px] font-mono text-white/30 w-10">
              {currentTrack?.isRadio ? "live" : formatTime(duration)}
            </span>
          </div>
        </div>

        {/* Volume & Right Equalizer Animation */}
        <div className="flex items-center justify-end gap-3 w-full md:w-1/4">
          <div className="hidden lg:flex items-center gap-1.5 h-6 px-3">
            {/* Minimal visual equalizer simulation */}
            {[1, 2, 3, 4, 5, 2, 4, 3, 1].map((height, i) => (
              <span 
                key={i} 
                className="w-0.5 bg-amber-500/60 rounded-full"
                style={{
                  height: isPlaying ? `${height * 4}px` : "2px",
                  animation: isPlaying ? `bounce 1s ease-in-out infinite alternate` : "none",
                  animationDelay: `${i * 0.1}s`
                }}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={toggleMute}
              className="text-white/40 hover:text-white transition-colors"
              title={isMuted ? "Включить звук" : "Выключить звук"}
            >
              {isMuted || volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input 
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-20 sm:w-24 h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-amber-550 outline-none"
              style={{
                background: `linear-gradient(to right, #d97706 0%, #d97706 ${(isMuted ? 0 : volume) * 100}%, rgba(255,255,255,0.1) ${(isMuted ? 0 : volume) * 100}%, rgba(255,255,255,0.1) 100%)`
              }}
            />
          </div>
        </div>

      </div>

      <style>{`
        @keyframes bounce {
          0% { height: 3px; }
          100% { height: 18px; }
        }
      `}</style>
    </div>
  );
}
