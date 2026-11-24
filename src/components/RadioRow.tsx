import React from "react";
import { Play, Pause, Radio, Waves, MapPin } from "lucide-react";
import { RadioStation } from "../types";

interface RadioRowProps {
  key?: any;
  station: RadioStation;
  index: number;
  isActive: boolean;
  isPlaying: boolean;
  onPlayToggle: () => void;
}

export default function RadioRow({
  station,
  index,
  isActive,
  isPlaying,
  onPlayToggle
}: RadioRowProps) {
  // Graceful fallback for favicon images
  const faviconUrl = station.favicon || "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=150&q=80";

  return (
    <div 
      className={`group flex items-center justify-between p-3 rounded-xl border border-transparent hover:border-white/10 transition-all duration-300 ${
        isActive 
          ? "bg-amber-950/25 border-amber-900/30 shadow-md shadow-amber-950/10" 
          : index % 2 === 0 
            ? "bg-white/5 hover:bg-white/10" 
            : "bg-transparent hover:bg-white/5"
      }`}
    >
      {/* Radio station artwork & info */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <span className="w-5 text-white/30 font-mono text-xs text-center hidden sm:block">
          {index + 1 < 10 ? `0${index + 1}` : index + 1}
        </span>
        <div className="relative w-12 h-12 rounded-lg flex-shrink-0 overflow-hidden border border-white/10 group-hover:border-white/20 bg-zinc-950 flex items-center justify-center">
          <img 
            src={faviconUrl} 
            alt={station.name} 
            referrerPolicy="no-referrer"
            onError={(e) => {
              // fallback if image fail to load
              (e.currentTarget as HTMLImageElement).src = "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=150&q=80";
            }}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />

          {/* Inline Hover Action trigger */}
          <div className={`absolute inset-0 bg-black/60 flex items-center justify-center transition-opacity ${
            isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          }`}>
            <button
              onClick={onPlayToggle}
              className="w-8 h-8 rounded-full bg-amber-600 hover:bg-amber-505 text-white flex items-center justify-center shadow-lg active:scale-90 transition-transform"
            >
              {isActive && isPlaying ? (
                <Pause className="w-4 h-4 fill-current text-white" />
              ) : (
                <Play className="w-4 h-4 fill-current text-white ml-0.5" />
              )}
            </button>
          </div>
        </div>

        <div className="min-w-0 select-none">
          <h4 className={`text-sm font-medium truncate ${isActive ? 'text-amber-500 font-semibold' : 'text-zinc-100'}`}>
            {station.name}
          </h4>
          <div className="flex flex-wrap items-center gap-x-2 text-xs text-white/40 mt-1">
            {station.country && (
              <span className="flex items-center gap-0.5 text-white/30">
                <MapPin className="w-3 h-3 text-white/20" />
                {station.country}
              </span>
            )}
            
            {station.tags && (
              <>
                <span className="text-white/10 hidden xs:inline">•</span>
                <span className="text-white/35 hidden xs:inline truncate max-w-[200px]" title={station.tags}>
                  {station.tags.split(",").slice(0, 3).join(", ")}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Bitrate & Quick button */}
      <div className="flex items-center gap-3 ml-4 col-span-1">
        {station.bitrate ? (
          <span className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-950/20 text-amber-500 border border-amber-900/30">
            <Waves className="w-3 h-3 opacity-60" /> {station.bitrate} kbps
          </span>
        ) : null}

        <button
          onClick={onPlayToggle}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 active:scale-95 transition-all ${
            isActive 
              ? "bg-amber-500/20 text-amber-500 border border-amber-500/30" 
              : "bg-white/5 hover:bg-white/10 text-white/80 hover:text-white"
          }`}
        >
          {isActive && isPlaying ? "ЭФИР" : <Radio className="w-3.5 h-3.5" />}
        </button>
      </div>

    </div>
  );
}
