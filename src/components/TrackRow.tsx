import React from "react";
import { Play, Pause, Star, Download, Trash2, CheckCircle, Music2, Loader2, Info } from "lucide-react";

interface TrackRowProps {
  key?: any;
  id: string | number;
  title: string;
  artist: string;
  artistId?: number;
  deezerId?: number;
  albumTitle?: string;
  albumCover?: string;
  previewUrl: string;
  index: number;
  isActive: boolean;
  isPlaying: boolean;
  isDownloaded: boolean;
  isDownloading: boolean;
  isWishlisted: boolean;
  showDelete?: boolean;
  onPlay: () => void;
  onWishlistToggle: () => void;
  onDownload: () => void;
  onDelete?: () => void;
  onSelectArtist?: (id: number, name: string) => void;
  onSelectAlbum?: (id: number) => void;
}

export default function TrackRow({
  id,
  title,
  artist,
  artistId,
  deezerId,
  albumTitle,
  albumCover,
  previewUrl,
  index,
  isActive,
  isPlaying,
  isDownloaded,
  isDownloading,
  isWishlisted,
  showDelete = false,
  onPlay,
  onWishlistToggle,
  onDownload,
  onDelete,
  onSelectArtist,
  onSelectAlbum
}: TrackRowProps) {
  const coverUrl = albumCover || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80";

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
      {/* Track Left Section (Artwork & Title) */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <span className="w-5 text-white/30 font-mono text-xs text-center hidden sm:block">
          {index + 1 < 10 ? `0${index + 1}` : index + 1}
        </span>
        <div className="relative w-12 h-12 rounded-lg flex-shrink-0 overflow-hidden border border-white/10 group-hover:border-white/20 bg-zinc-950 flex items-center justify-center">
          {coverUrl ? (
            <img 
              src={coverUrl} 
              alt={title} 
              referrerPolicy="no-referrer"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <Music2 className="w-5 h-5 text-zinc-650" />
          )}

          {/* Inline Hover Play/Pause trigger */}
          <div className={`absolute inset-0 bg-black/60 flex items-center justify-center transition-opacity ${
            isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          }`}>
            <button
              onClick={onPlay}
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
            {title}
          </h4>
          <div className="flex flex-wrap items-center gap-x-2 text-xs text-white/40 mt-1">
            {artistId && onSelectArtist ? (
              <button
                onClick={() => onSelectArtist(artistId, artist)}
                className="hover:text-amber-500 font-medium truncate inline-block text-left hover:underline cursor-pointer"
              >
                {artist}
              </button>
            ) : (
              <span className="truncate">{artist}</span>
            )}

            {albumTitle && (
              <>
                <span className="text-white/20 hidden xs:inline">•</span>
                <span className="text-white/30 hidden xs:inline truncate max-w-[150px]">
                  {albumTitle}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Options Right Section */}
      <div className="flex items-center gap-1 sm:gap-2 ml-4">
        {/* Play indicator label/badge */}
        {isDownloaded && (
          <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <CheckCircle className="w-3 h-3" /> MP3
          </span>
        )}

        {/* Favorite Star action */}
        {deezerId && (
          <button
            onClick={onWishlistToggle}
            className={`p-2 rounded-lg hover:bg-white/5 transition-colors ${
              isWishlisted 
                ? "text-amber-500" 
                : "text-white/45 hover:text-amber-500"
            }`}
            title={isWishlisted ? "Удалить из избранного" : "Добавить в избранное"}
          >
            <Star className={`w-4 h-4 ${isWishlisted ? "fill-current" : ""}`} />
          </button>
        )}

        {/* Download Action button */}
        {isDownloading ? (
          <div className="p-2 text-amber-500 antialiased animate-spin">
            <Loader2 className="w-4 h-4" />
          </div>
        ) : isDownloaded ? (
          <button
            disabled
            className="p-2 text-emerald-500 bg-emerald-950/20 rounded-lg cursor-not-allowed"
            title="Скачано"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={onDownload}
            className="p-2 text-white/45 hover:text-amber-500 hover:bg-white/5 rounded-lg transition-all"
            title="Скачать в Мои аудио"
          >
            <Download className="w-4 h-4" />
          </button>
        )}

        {/* Artist Search / Info clicker */}
        {artistId && onSelectArtist && (
          <button
            onClick={() => onSelectArtist(artistId, artist)}
            className="p-2 text-white/45 hover:text-white hover:bg-white/5 rounded-lg hidden md:block transition-colors"
            title="Информация об исполнителе"
          >
            <Info className="w-4 h-4" />
          </button>
        )}

        {/* Local Delete Trash Icon */}
        {showDelete && onDelete && (
          <button
            onClick={onDelete}
            className="p-2 text-white/45 hover:text-red-400 hover:bg-red-950/10 rounded-lg transition-colors"
            title="Удалить трек из библиотеки"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
