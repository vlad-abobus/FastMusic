import React, { useState, useEffect, useRef } from "react";
import { 
  Music, Radio, Heart, Library, Search, Flame, Sliders, 
  Menu, X, Sparkles, LogOut, Check, ArrowLeft, Disc, Users,
  FolderHeart, Info, Volume2, CloudLightning, DownloadCloud, AlertTriangle
} from "lucide-react";

import { 
  LocalTrack, WishlistTrack, RadioStation, 
  ActiveTab, SearchFilter, PlaybackItem,
  DeezerTrack, DeezerAlbum, DeezerArtist
} from "./types";
import AudioPlayer from "./components/AudioPlayer";
import TrackRow from "./components/TrackRow";
import RadioRow from "./components/RadioRow";

export default function App() {
  // Navigation & View active state
  const [activeTab, setActiveTab] = useState<ActiveTab>("charts");
  const [selectedArtist, setSelectedArtist] = useState<{ id: number; name: string } | null>(null);
  const [selectedAlbum, setSelectedAlbum] = useState<{ id: number; title: string; cover: string } | null>(null);
  
  // Player state
  const [currentTrack, setCurrentTrack] = useState<PlaybackItem | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playQueue, setPlayQueue] = useState<PlaybackItem[]>([]);
  const [queueIndex, setQueueIndex] = useState<number>(-1);

  // Search filter options
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchFilter, setSearchFilter] = useState<SearchFilter>("all");
  const [searchTriggered, setSearchTriggered] = useState<boolean>(false);

  // API content states
  const [charts, setCharts] = useState<any[]>([]);
  const [library, setLibrary] = useState<LocalTrack[]>([]);
  const [wishlist, setWishlist] = useState<WishlistTrack[]>([]);
  const [radioStations, setRadioStations] = useState<RadioStation[]>([]);
  const [radioSearchMode, setRadioSearchMode] = useState<"byname" | "bytag" | "bycountry">("byname");

  // Detailed views
  const [artistTracks, setArtistTracks] = useState<any[]>([]);
  const [artistRelated, setArtistRelated] = useState<any[]>([]);
  const [artistInfo, setArtistInfo] = useState<any | null>(null);
  const [albumDetails, setAlbumDetails] = useState<any | null>(null);

  // Loading states
  const [loading, setLoading] = useState<boolean>(false);
  const [downloadingIds, setDownloadingIds] = useState<Record<string, boolean>>({});
  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Mobile menu toggle
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  // Auto-fetch standard collections on mount
  useEffect(() => {
    fetchCharts();
    fetchLibrary();
    fetchWishlist();
  }, []);

  // Update background queue index if currentTrack changes
  useEffect(() => {
    if (currentTrack && playQueue.length > 0) {
      const idx = playQueue.findIndex(item => item.id === currentTrack.id);
      if (idx !== -1) setQueueIndex(idx);
    }
  }, [currentTrack, playQueue]);

  // Helpers to introduce premium deliberate delays
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const showError = (msg: string) => {
    setErrorNotice(msg);
    setTimeout(() => setErrorNotice(null), 5500);
  };

  // ──── API ACTIONS ────

  const fetchCharts = async () => {
    setLoading(true);
    setErrorNotice(null);
    try {
      const res = await fetch("/api/deezer/charts");
      if (!res.ok) throw new Error("Ошибка загрузки чартов");
      const data = await res.json();
      
      // Delay to ensure smooth images preload and eliminate visual layout shifts
      await delay(350);

      if (data && data.data) {
        setCharts(data.data);
      }
    } catch (err: any) {
      showError(err.message || "Не удалось загрузить чарты Deezer");
    } finally {
      setLoading(false);
    }
  };

  const fetchLibrary = async () => {
    let serverLibrary: LocalTrack[] = [];
    try {
      const res = await fetch("/api/library");
      if (res.ok) {
        serverLibrary = await res.json();
      }
    } catch (err) {
      console.warn("Backend unavailable for fetchLibrary, using local fallbacks", err);
    }

    let clientLibrary: LocalTrack[] = [];
    try {
      const offlineSaved = localStorage.getItem("CLIENT_LOCAL_LIBRARY");
      if (offlineSaved) {
        clientLibrary = JSON.parse(offlineSaved) as LocalTrack[];
      }
    } catch (e) {
      console.error("Failed to parse CLIENT_LOCAL_LIBRARY", e);
    }

    const mergedMap = new Map<string, LocalTrack>();
    serverLibrary.forEach(t => mergedMap.set(String(t.id), t));
    clientLibrary.forEach(t => mergedMap.set(String(t.id), t));

    setLibrary(Array.from(mergedMap.values()));
  };

  const fetchWishlist = async () => {
    let serverWishlist: WishlistTrack[] = [];
    try {
      const res = await fetch("/api/wishlist");
      if (res.ok) {
        serverWishlist = await res.json();
      }
    } catch (err) {
      console.warn("Backend unavailable for fetchWishlist, using local fallbacks", err);
    }

    let clientWishlist: WishlistTrack[] = [];
    try {
      const offlineWish = localStorage.getItem("CLIENT_WISHLIST");
      if (offlineWish) {
        clientWishlist = JSON.parse(offlineWish) as WishlistTrack[];
      }
    } catch (e) {
      console.error("Failed to parse CLIENT_WISHLIST", e);
    }

    const mergedWishMap = new Map<number, WishlistTrack>();
    serverWishlist.forEach(w => mergedWishMap.set(w.deezer_id, w));
    clientWishlist.forEach(w => mergedWishMap.set(w.deezer_id, w));

    setWishlist(Array.from(mergedWishMap.values()));
  };

  // Trigger search on return or click
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setErrorNotice(null);
    setSearchTriggered(true);
    setSelectedArtist(null);
    setSelectedAlbum(null);

    try {
      const res = await fetch(`/api/deezer/search?q=${encodeURIComponent(searchQuery)}&type=${searchFilter === "all" ? "tracks" : searchFilter}`);
      if (!res.ok) throw new Error("Ошибка поиска");
      const data = await res.json();
      
      await delay(350);

      if (data && data.data) {
        setCharts(data.data);
        setActiveTab("charts");
      }
    } catch (err: any) {
      showError(err.message || "Поиск завершился ошибкой");
    } finally {
      setLoading(false);
    }
  };

  // Reset Search to defaults
  const handleResetSearch = () => {
    setSearchQuery("");
    setSearchTriggered(false);
    fetchCharts();
  };

  // Fetch Artist Info, Top Tracks and Related Music
  const handleSelectArtist = async (id: number, name: string) => {
    setLoading(true);
    setErrorNotice(null);
    setSelectedArtist({ id, name });
    setSelectedAlbum(null);
    setActiveTab("artist");
    setMobileMenuOpen(false);

    try {
      const [trackRes, relatedRes, infoRes] = await Promise.all([
        fetch(`/api/deezer/artist/${id}/top`),
        fetch(`/api/deezer/artist/${id}/related`),
        fetch(`/api/deezer/artist/${id}`)
      ]);

      await delay(350);

      if (trackRes.ok) {
        const data = await trackRes.json();
        setArtistTracks(data.data || []);
      }
      if (relatedRes.ok) {
        const data = await relatedRes.json();
        setArtistRelated(data.data || []);
      }
      if (infoRes.ok) {
        const data = await infoRes.json();
        setArtistInfo(data);
      }
    } catch (err: any) {
      showError("Не удалось загрузить карточку исполнителя");
    } finally {
      setLoading(false);
    }
  };

  // Fetch Album Contents
  const handleSelectAlbum = async (id: number) => {
    setLoading(true);
    setErrorNotice(null);
    setSelectedAlbum({ id, title: "", cover: "" });
    setSelectedArtist(null);
    setActiveTab("album");

    try {
      const res = await fetch(`/api/deezer/album/${id}`);
      if (!res.ok) throw new Error("Не удалось загрузить треклист альбома");
      const data = await res.json();
      
      await delay(350);
      setAlbumDetails(data);
    } catch (err: any) {
      showError(err.message);
      setActiveTab("charts");
    } finally {
      setLoading(false);
    }
  };

  // Radio Handling: fetch popular
  const fetchPopularRadio = async () => {
    setLoading(true);
    setErrorNotice(null);
    try {
      const res = await fetch("/api/radio/popular");
      if (!res.ok) throw new Error("Ошибка соединения с Radio Browser");
      const data = await res.json();
      
      await delay(350);
      setRadioStations(data || []);
    } catch (err: any) {
      showError("Не удалось загрузить популярные радиостанции");
    } finally {
      setLoading(false);
    }
  };

  // Radio Search
  const handleRadioSearch = async (query: string) => {
    if (!query.trim()) {
      fetchPopularRadio();
      return;
    }
    setLoading(true);
    setErrorNotice(null);
    try {
      const res = await fetch(`/api/radio/search?q=${encodeURIComponent(query)}&mode=${radioSearchMode}`);
      if (!res.ok) throw new Error("Станции не найдены");
      const data = await res.json();
      
      await delay(350);
      setRadioStations(data || []);
    } catch (err: any) {
      showError("Ошибка поиска радиостанций");
    } finally {
      setLoading(false);
    }
  };

  // Download Track MP3 Handler with elegant server fallback download
  const handleDownloadTrack = async (item: any) => {
    const trackId = item.id;
    const isLocalTrack = String(trackId).startsWith("local_");
    if (isLocalTrack) return; // already a downloaded asset

    setDownloadingIds(prev => ({ ...prev, [trackId]: true }));
    showToast(`Запуск скачивания: ${item.artist?.name || item.artist} — ${item.title}`);

    await delay(200);

    try {
      const res = await fetch("/api/library/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: item.title,
          artist: item.artist?.name || item.artist,
          album_art: item.album?.cover_medium || item.album_art,
          preview_url: item.preview || item.preview_url,
          deezer_id: item.id
        })
      });

      if (!res.ok) throw new Error("Не удалось скачать трек через сервер");
      
      const resData = await res.json();
      showToast(`Скачано успешно! ${item.title}`);
      await fetchLibrary(); // refresh downloaded listings
    } catch (err: any) {
      console.warn("Backend downloader failed/offline, switching to frontend storage fallback...", err);
      showToast("Автономный режим: сохраняем в локальный буфер браузера...");
      await delay(200);

      try {
        const offlineSaved = localStorage.getItem("CLIENT_LOCAL_LIBRARY");
        let clientLibrary: LocalTrack[] = offlineSaved ? JSON.parse(offlineSaved) : [];

        const isAlreadyInClientLib = clientLibrary.some(
          t => t.deezer_id === item.id || (t.title.toLowerCase() === item.title.toLowerCase() && t.artist.toLowerCase() === (item.artist?.name || item.artist || "").toLowerCase())
        );

        if (!isAlreadyInClientLib) {
          const clientTrack: LocalTrack = {
            id: `local_client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
            title: item.title,
            artist: item.artist?.name || item.artist,
            album_art: item.album?.cover_medium || item.album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
            file_path: "", 
            deezer_id: item.id,
            preview_url: item.preview || item.preview_url || "",
            duration: 30
          };
          clientLibrary.push(clientTrack);
          localStorage.setItem("CLIENT_LOCAL_LIBRARY", JSON.stringify(clientLibrary));
        }

        showToast(`Успешно сохранено локально на клиенте! ${item.title}`);
        await fetchLibrary();
      } catch (clientErr) {
        showError(`Не удалось скачать: ${item.title}`);
      }
    } finally {
      setDownloadingIds(prev => ({ ...prev, [trackId]: false }));
    }
  };

  // Wishlist Add/Remove Toggle with server-unavailable cache support and download suggestion
  const handleWishlistToggle = async (item: any) => {
    const isFavorite = wishlist.some(w => w.deezer_id === item.id);

    if (isFavorite) {
      // Remove from favorites
      try {
        const res = await fetch(`/api/wishlist/${item.id}`, { method: "DELETE" });
        if (res.ok) {
          showToast(`Удалено из избранного: ${item.title}`);
          await fetchWishlist();
          return;
        }
      } catch (err) {
        console.warn("Wishlist remove server failed, attempting client fallback", err);
      }

      try {
        const offlineWish = localStorage.getItem("CLIENT_WISHLIST");
        let clientWish: any[] = offlineWish ? JSON.parse(offlineWish) : [];
        clientWish = clientWish.filter(w => w.deezer_id !== item.id);
        localStorage.setItem("CLIENT_WISHLIST", JSON.stringify(clientWish));
        showToast(`Удалено из избранного: ${item.title}`);
        await fetchWishlist();
      } catch (e) {
        showError("Ошибка удаления из избранного");
      }
    } else {
      // Add to favorites
      let addedSuccess = false;
      try {
        const res = await fetch("/api/wishlist", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: item.title,
            artist: item.artist?.name || item.artist,
            album_art: item.album?.cover_medium || item.album_art,
            preview_url: item.preview || item.preview_url,
            deezer_id: item.id
          })
        });

        if (res.ok) {
          showToast(`Добавлено в избранное: ${item.title}`);
          await fetchWishlist();
          addedSuccess = true;
        }
      } catch (err) {
        console.warn("Wishlist save server failed, attempting client fallback", err);
      }

      if (!addedSuccess) {
        try {
          const offlineWish = localStorage.getItem("CLIENT_WISHLIST");
          let clientWish: any[] = offlineWish ? JSON.parse(offlineWish) : [];
          const isAlreadyInOfflineWish = clientWish.some(w => w.deezer_id === item.id);
          
          if (!isAlreadyInOfflineWish) {
            clientWish.push({
              id: `wish_client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
              title: item.title,
              artist: item.artist?.name || item.artist,
              album_art: item.album?.cover_medium || item.album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
              preview_url: item.preview || item.preview_url || "",
              deezer_id: item.id
            });
            localStorage.setItem("CLIENT_WISHLIST", JSON.stringify(clientWish));
          }
          showToast(`Добавлено в избранное: ${item.title}`);
          await fetchWishlist();
          addedSuccess = true;
        } catch (e) {
          showError("Ошибка добавления в избранное");
        }
      }

      // Propose download if not already in library
      if (addedSuccess) {
        const isDownloaded = library.some(t => 
          t.deezer_id === item.id || 
          (t.title.toLowerCase() === item.title.toLowerCase() && 
           t.artist.toLowerCase() === (item.artist?.name || item.artist || "").toLowerCase())
        );
        if (!isDownloaded) {
          setTimeout(() => {
            const wantDownload = window.confirm(`Добавлено в избранное!\n\nХотите скачать песню "${item.title}" в "Мои аудио", чтобы слушать её полностью, а не 30-секундное превью?`);
            if (wantDownload) {
              handleDownloadTrack(item);
            }
          }, 350);
        }
      }
    }
  };

  // Physical local track removal from My Audio library
  const handleDeleteLocalTrack = async (id: string, name: string) => {
    if (!confirm(`Вы действительно хотите удалить трек "${name}" из локальной библиотеки?`)) return;

    if (String(id).startsWith("local_client_")) {
      try {
        const offlineSaved = localStorage.getItem("CLIENT_LOCAL_LIBRARY");
        if (offlineSaved) {
          let clientLibrary = JSON.parse(offlineSaved) as LocalTrack[];
          clientLibrary = clientLibrary.filter(t => t.id !== id);
          localStorage.setItem("CLIENT_LOCAL_LIBRARY", JSON.stringify(clientLibrary));
          
          showToast(`Удален клиентский файл трека: ${name}`);
          if (currentTrack?.localId === id) {
            setCurrentTrack(null);
            setIsPlaying(false);
          }
          await fetchLibrary();
        }
      } catch (err) {
        showError("Не удалось удалить локальный файл");
      }
      return;
    }

    try {
      const res = await fetch(`/api/library/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast(`Удален файл трека: ${name}`);
        if (currentTrack?.localId === id) {
          setCurrentTrack(null);
          setIsPlaying(false);
        }
        await fetchLibrary();
      } else {
        const offlineSaved = localStorage.getItem("CLIENT_LOCAL_LIBRARY");
        if (offlineSaved) {
          let clientLibrary = JSON.parse(offlineSaved) as LocalTrack[];
          clientLibrary = clientLibrary.filter(t => t.id !== id);
          localStorage.setItem("CLIENT_LOCAL_LIBRARY", JSON.stringify(clientLibrary));
        }
        await fetchLibrary();
      }
    } catch (err) {
      console.warn("Server delete offline, removing client side backup", err);
      const offlineSaved = localStorage.getItem("CLIENT_LOCAL_LIBRARY");
      if (offlineSaved) {
        let clientLibrary = JSON.parse(offlineSaved) as LocalTrack[];
        clientLibrary = clientLibrary.filter(t => t.id !== id);
        localStorage.setItem("CLIENT_LOCAL_LIBRARY", JSON.stringify(clientLibrary));
      }
      await fetchLibrary();
    }
  };

  // ──── PLAYBACK & QUEUE LOGIC ────

  // Play a song
  const handlePlaySong = (track: any, sourceList: any[]) => {
    const findDownloaded = (item: any) => {
      const itemId = Number(item.deezer_id || item.id);
      return library.find(libTrack => 
        (libTrack.deezer_id && libTrack.deezer_id === itemId) ||
        (itemId && libTrack.deezer_id === itemId) ||
        (libTrack.title.toLowerCase() === item.title.toLowerCase() &&
         libTrack.artist.toLowerCase() === (item.artist?.name || item.artist || "").toLowerCase())
      );
    };

    const downloadedMain = findDownloaded(track);
    let playUrl = track.preview || track.preview_url;
    let localIdVal = String(track.id).startsWith("local_") ? track.id : undefined;

    if (downloadedMain) {
      if (downloadedMain.file_path) {
        playUrl = `/api/library/stream/${downloadedMain.id}`;
      } else {
        playUrl = downloadedMain.preview_url || playUrl;
      }
      localIdVal = downloadedMain.id;
    } else if (track.file_path || String(track.id).startsWith("local_")) {
      playUrl = `/api/library/stream/${track.id}`;
    }

    const playItem: PlaybackItem = {
      id: track.id,
      title: track.title,
      artist: track.artist?.name || track.artist,
      album_art: track.album?.cover_medium || track.album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
      url: playUrl,
      deezer_id: track.deezer_id || (typeof track.id === "number" ? track.id : undefined),
      localId: localIdVal
    };

    // Construct playing queue from current selection source
    const queueItems: PlaybackItem[] = sourceList.map(item => {
      const downloadedItem = findDownloaded(item);
      let url = item.preview || item.preview_url;
      let lid = String(item.id).startsWith("local_") ? item.id : undefined;

      if (downloadedItem) {
        if (downloadedItem.file_path) {
          url = `/api/library/stream/${downloadedItem.id}`;
        } else {
          url = downloadedItem.preview_url || url;
        }
        lid = downloadedItem.id;
      } else if (item.file_path || String(item.id).startsWith("local_")) {
        url = `/api/library/stream/${item.id}`;
      }

      return {
        id: item.id,
        title: item.title,
        artist: item.artist?.name || item.artist,
        album_art: item.album?.cover_medium || item.album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
        url: url,
        deezer_id: item.deezer_id || (typeof item.id === "number" ? item.id : undefined),
        localId: lid
      };
    });

    setPlayQueue(queueItems);
    setCurrentTrack(playItem);
    setIsPlaying(true);
  };

  // Play direct live radio stream
  const handlePlayRadio = (station: RadioStation) => {
    const radioItem: PlaybackItem = {
      id: station.stationuuid,
      title: station.name,
      artist: station.country ? `Радиостанция • ${station.country}` : "Live Радио",
      album_art: station.favicon || "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=150&q=80",
      url: station.url_resolved || station.url,
      isRadio: true
    };

    setPlayQueue([radioItem]);
    setCurrentTrack(radioItem);
    setIsPlaying(true);
    showToast(`Слушаем радио: ${station.name}`);
  };

  const handleNextTrack = () => {
    if (playQueue.length <= 1 || queueIndex === -1) return;
    const nextIdx = (queueIndex + 1) % playQueue.length;
    setCurrentTrack(playQueue[nextIdx]);
    setIsPlaying(true);
  };

  const handlePrevTrack = () => {
    if (playQueue.length <= 1 || queueIndex === -1) return;
    const prevIdx = (queueIndex - 1 + playQueue.length) % playQueue.length;
    setCurrentTrack(playQueue[prevIdx]);
    setIsPlaying(true);
  };

  const handleToggleTab = (tab: ActiveTab) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
    setSelectedArtist(null);
    setSelectedAlbum(null);

    // Dynamic initial loading on selection if not loaded
    if (tab === "radio" && radioStations.length === 0) {
      fetchPopularRadio();
    } else if (tab === "library") {
      fetchLibrary();
    } else if (tab === "wishlist") {
      fetchWishlist();
    }
  };

  return (
    <div id="fastmusic-root" className="min-h-screen bg-[#050505] text-zinc-100 flex flex-col font-sans select-none antialiased">
      
      {/* ──── TOP BANNER / GLASS HEADER NOTICE ──── */}
      {errorNotice && (
        <div className="bg-red-500/10 border-b border-red-500/20 text-white px-4 py-2 text-xs flex items-center justify-between animate-fade-in z-50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>{errorNotice}</span>
          </div>
          <button onClick={() => setErrorNotice(null)} className="p-1 hover:text-white">&times;</button>
        </div>
      )}

      {/* Floating Status Toast notification */}
      {toastMessage && (
        <div className="fixed bottom-24 right-4 bg-zinc-950 border border-white/10 text-white shadow-2xl px-4 py-3 rounded-xl flex items-center gap-2 animate-bounce z-50">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Main full-scale application wrapper (sidebar + content workspace) */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ──── DESKTOP SIDEBAR ──── */}
        <aside id="desktop-sidebar" className="w-[260px] bg-[#070707] border-r border-white/5 flex-shrink-0 flex flex-col justify-between hidden md:flex">
          
          <div>
            {/* BRANDING LOGO */}
            <div className="p-6 flex items-center gap-3 border-b border-white/5">
              <div className="w-10 h-10 bg-gradient-to-tr from-amber-600 to-amber-700/80 rounded-xl flex items-center justify-center text-white shadow-lg shadow-amber-950/20">
                <Music className="w-5 h-5 fill-current animate-pulse text-zinc-950" />
              </div>
              <div>
                <h1 className="font-serif italic font-bold text-lg tracking-wide text-amber-500">
                  FastMusic
                </h1>
                <p className="text-[10px] text-zinc-500 tracking-widest uppercase font-semibold">VK Music Clone</p>
              </div>
            </div>

            {/* NAVIGATION MODULES */}
            <nav className="p-4 space-y-1">
              <button 
                onClick={() => handleToggleTab("charts")}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "charts" 
                    ? "bg-amber-653 text-white shadow-lg shadow-amber-950/20" 
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Flame className="w-4 h-4" />
                  <span>Чарты и новинки</span>
                </div>
                <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-white font-mono">charts</span>
              </button>

              <button 
                onClick={() => handleToggleTab("library")}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "library"
                    ? "bg-amber-653 text-white shadow-lg shadow-amber-950/20" 
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Library className="w-4 h-4" />
                  <span>Мои аудио (MP3)</span>
                </div>
                <span className="text-[11px] font-bold text-amber-505">{library.length}</span>
              </button>

              <button 
                onClick={() => handleToggleTab("wishlist")}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "wishlist" 
                    ? "bg-amber-653 text-white shadow-lg shadow-amber-950/20" 
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Heart className="w-4 h-4" />
                  <span>Избранное</span>
                </div>
                <span className="text-[11px] text-amber-500 font-bold">&#9733; {wishlist.length}</span>
              </button>

              <button 
                onClick={() => handleToggleTab("radio")}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "radio" 
                    ? "bg-amber-653 text-white shadow-lg shadow-amber-950/20" 
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Radio className="w-4 h-4" />
                  <span>Интернет-Радио</span>
                </div>
                <span className="px-1 py-0.5 text-[9px] font-bold text-amber-500 bg-amber-500/10 rounded">LIVE</span>
              </button>
            </nav>
          </div>

          {/* SIDEBAR FOOTER (LOCAL LIBRARY STATS CARD) */}
          <div className="p-4">
            <div className="bg-gradient-to-b from-white/5 to-transparent border border-white/10 p-4 rounded-2xl select-none">
              <div className="flex items-center gap-2 text-amber-500">
                <Check className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Офлайн-библиотека</span>
              </div>
              <p className="text-[11px] text-white/40 mt-1.5 leading-relaxed">
                Скачивайте любые песни в формате MP3. Они сохраняются локально на сервере и доступны для мгновенного прослушивания.
              </p>
              <div className="mt-3 flex items-center justify-between text-xs font-medium border-t border-white/5 pt-2">
                <span className="text-white/40">Файлов MP3:</span>
                <span className="text-amber-500 font-mono font-bold">{library.length}</span>
              </div>
            </div>
            
            <p className="text-[9px] text-[#555] text-center mt-4 tracking-widest font-mono">MADE FOR MAGDEVICE</p>
          </div>
        </aside>

        {/* ──── CONTENT PANE WORKSPACE ──── */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          
          {/* Header Bar containing Search inputs & mobile toggle Hamburger Menu */}
          <header className="bg-[#050505]/95 sticky top-0 z-40 backdrop-blur-md border-b border-white/5 p-4 flex items-center justify-between gap-4">
            
            {/* Mobile menu Toggle Button */}
            <div className="flex items-center gap-3 md:hidden">
              <button 
                onClick={() => setMobileMenuOpen(true)}
                className="p-2 text-white/60 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5" />
              </button>
              <h2 className="font-serif italic font-bold text-sm tracking-wide text-amber-500">FastMusic</h2>
            </div>

            {/* REST SEARCH CONTROLLER */}
            <form onSubmit={handleSearchSubmit} className="flex-1 max-w-xl flex items-center bg-white/5 border border-white/10 focus-within:border-amber-500/50 rounded-xl px-3 py-1.5 transition-all">
              <Search className="w-4 h-4 text-zinc-500 mr-2 flex-shrink-0" />
              <input
                type="text"
                placeholder={activeTab === "radio" ? "Поиск радиостанций по названию, стране или тегу..." : "Ищите популярные треки, альбомы и новинки..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent border-none text-zinc-100 placeholder-zinc-500 text-sm focus:outline-none focus:ring-0 mr-2"
              />
              {searchQuery && (
                <button 
                  type="button" 
                  onClick={handleResetSearch}
                  className="p-1 hover:text-white text-zinc-500 text-xs text-semibold cursor-pointer underline flex-shrink-0 mr-1"
                >
                  Сбросить
                </button>
              )}
              
              {/* Filter tabs */}
              {activeTab !== "radio" ? (
                <select 
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value as SearchFilter)}
                  className="bg-black border-l border-white/10 text-zinc-400 text-xs font-semibold py-1 pl-2 pr-1 focus:outline-none focus:text-white cursor-pointer hidden sm:block"
                >
                  <option value="all">Все треки</option>
                  <option value="albums">Альбомы</option>
                  <option value="artists">Исполнители</option>
                </select>
              ) : null}

              <button 
                type="submit"
                className="bg-amber-600 hover:bg-amber-505 text-white rounded-lg px-3 py-1 text-xs font-bold shadow-md transition-colors"
              >
                Поиск
              </button>
            </form>

            <div className="hidden sm:flex items-center gap-3 text-xs text-white/40 select-none">
              <Check className="w-4 h-4 text-amber-500" />
              <span>Станция Онлайн</span>
            </div>

          </header>

          {/* ──── CONTENT SCROLLER CONTAINER ──── */}
          <div className="flex-1 p-4 md:p-6 lg:p-8 space-y-6 animate-fade-in">
            
            {/* DISPLAY PRE-LOAD SKELETON TO AVOID COVER ART RENDER SHIFT/LAG */}
            {loading ? (
              <div className="space-y-4 animate-pulse">
                {/* Header banner skeleton */}
                <div className="bg-white/5 border border-white/5 p-6 md:p-8 rounded-3xl h-40 w-full mb-6 flex flex-col justify-end gap-2">
                  <div className="h-4 bg-white/10 rounded w-1/4" />
                  <div className="h-8 bg-white/10 rounded w-1/2" />
                  <div className="h-3 bg-white/5 rounded w-1/3" />
                </div>
                {/* Track rows skeletons */}
                <div className="space-y-2">
                  <div className="h-3 bg-white/5 rounded w-24 mb-4" />
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-transparent">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="w-5 h-4 bg-white/10 rounded hidden sm:block" />
                        <div className="w-12 h-12 rounded-lg bg-white/10 flex-shrink-0" />
                        <div className="space-y-2 flex-1 max-w-[200px]">
                          <div className="h-3.5 bg-white/10 rounded w-3/4" />
                          <div className="h-2.5 bg-white/5 rounded w-1/2" />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <div className="w-8 h-8 rounded-lg bg-white/5" />
                        <div className="w-8 h-8 rounded-lg bg-white/5" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {/* ──── TAB DISPLAY MODULES ──── */}
                
                {/* 1. CHARTS & DEEZER RESULT GRID */}
                {activeTab === "charts" && (
                  <div className="space-y-4 animate-fade-in" id="tab-charts-display">
                    
                    {/* Visual header panel */}
                    <div className="bg-gradient-to-r from-amber-950/20 via-[#0a0a0a] to-[#0c0c0c] border border-white/5 p-6 md:p-8 rounded-3xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl shadow-black">
                      <div className="relative z-10 text-center md:text-left space-y-2">
                        <span className="px-2.5 py-1 text-[10px] font-bold bg-amber-500/10 text-amber-500 rounded-full border border-amber-500/20 uppercase tracking-widest font-mono">
                          Главные Чарты
                        </span>
                        <h2 className="text-2xl md:text-3.5xl font-serif font-medium tracking-tight text-white mt-1">
                          {searchTriggered ? `Результаты по запросу "${searchQuery}"` : "Сегодняшний ТОП Чарта"}
                        </h2>
                        <p className="text-white/40 text-xs md:text-sm max-w-md">
                          Подробный список самого популярного мирового контента по версии Deezer. Слушайте превью или скачивайте к себе!
                        </p>
                      </div>

                      <div className="relative group w-24 h-24 hidden md:flex items-center justify-center">
                        <Disc className="w-20 h-20 text-amber-500/10 animate-[spin_12s_linear_infinite]" />
                        <Sparkles className="w-6 h-6 text-amber-500 absolute animate-pulse" />
                      </div>
                    </div>

                    {/* Chart list section */}
                    <div className="space-y-2">
                      <h3 className="text-zinc-400 text-xs font-bold uppercase tracking-wider mb-2">ПОПУЛЯРНАЯ МУЗЫКА</h3>
                      
                      {charts.length === 0 ? (
                        <div className="bg-zinc-950 border border-zinc-900 rounded-2xl p-8 text-center text-zinc-500 text-sm">
                          Ничего не найдено. Пожалуйста, попробуйте другой запрос.
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 gap-2">
                          {charts.map((track, i) => {
                            // Check if current track selection is active
                            const isActive = currentTrack?.id === track.id;
                            const isDownloaded = library.some(l => l.deezer_id === track.id || (l.artist.toLowerCase() === (track.artist?.name || "").toLowerCase() && l.title.toLowerCase() === track.title.toLowerCase()));
                            const isDownloading = !!downloadingIds[track.id];
                            const isWishlisted = wishlist.some(w => w.deezer_id === track.id);

                            return (
                              <TrackRow 
                                key={track.id}
                                id={track.id}
                                title={track.title}
                                artist={track.artist?.name || track.artist}
                                artistId={track.artist?.id}
                                deezerId={track.id}
                                albumCover={track.album?.cover_medium}
                                albumTitle={track.album?.title}
                                previewUrl={track.preview}
                                index={i}
                                isActive={isActive}
                                isPlaying={isPlaying}
                                isDownloaded={isDownloaded}
                                isDownloading={isDownloading}
                                isWishlisted={isWishlisted}
                                onPlay={() => handlePlaySong(track, charts)}
                                onWishlistToggle={() => handleWishlistToggle(track)}
                                onDownload={() => handleDownloadTrack(track)}
                                onSelectArtist={(id, name) => handleSelectArtist(id, name)}
                                onSelectAlbum={(id) => handleSelectAlbum(id)}
                              />
                            );
                          })}
                        </div>
                      )}
                    </div>

                  </div>
                )}

                {/* 2. LIBRARY (LOCAL MP3 DOWNLOADS) */}
                {activeTab === "library" && (
                  <div className="space-y-4 animate-fade-in" id="tab-library-display">
                    
                    <div className="flex items-center justify-between border-b border-white/5 pb-3">
                      <div>
                        <h2 className="text-xl md:text-2xl font-serif font-medium tracking-tight text-white flex items-center gap-2">
                          <Library className="w-5 h-5 text-amber-500" />
                          Мои аудио (MP3 файлы)
                        </h2>
                        <p className="text-xs text-white/40 mt-1">
                          Загруженные на сервер высококачественные аудиофайлы, которые транслируются с поддержкой перемотки.
                        </p>
                      </div>
                      <span className="text-xs font-bold text-white/60 bg-white/5 border border-white/10 px-3 py-1.5 rounded-xl font-mono">
                        {library.length} треков
                      </span>
                    </div>

                    {library.length === 0 ? (
                      <div className="bg-transparent border border-white/5 border-dashed rounded-3xl p-12 text-center flex flex-col items-center justify-center gap-3">
                        <DownloadCloud className="w-10 h-10 text-white/10 animate-bounce" />
                        <h3 className="font-bold text-sm text-zinc-300">Локальная медиатека пуста</h3>
                        <p className="text-white/30 text-xs max-w-sm">
                          Перейдите в чарты, найдите любимые песни и нажмите кнопку скачивания (⬇), чтобы загрузить их в высоком качестве.
                        </p>
                        <button 
                          onClick={() => handleToggleTab("charts")}
                          className="mt-2 bg-amber-600 hover:bg-amber-505 text-white rounded-xl px-4 py-2 text-xs font-semibold shadow"
                        >
                          Посмотреть чарты
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        {library.map((track, i) => {
                          const isActive = currentTrack?.id === track.id || currentTrack?.localId === track.id;
                          const isWishlisted = wishlist.some(w => w.deezer_id === track.deezer_id);

                          return (
                            <TrackRow 
                              key={track.id}
                              id={track.id}
                              title={track.title}
                              artist={track.artist}
                              deezerId={track.deezer_id}
                              albumCover={track.album_art}
                              previewUrl={track.preview_url || ""}
                              index={i}
                              isActive={isActive}
                              isPlaying={isPlaying}
                              isDownloaded={true}
                              isDownloading={false}
                              isWishlisted={isWishlisted}
                              showDelete={true}
                              onPlay={() => handlePlaySong(track, library)}
                              onWishlistToggle={() => handleWishlistToggle({ id: track.deezer_id, title: track.title, artist: track.artist, album: { cover_medium: track.album_art }, preview: track.preview_url })}
                              onDownload={() => {}}
                              onDelete={() => handleDeleteLocalTrack(track.id, track.title)}
                            />
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* 3. WISHLIST FAVORITES */}
                {activeTab === "wishlist" && (
                  <div className="space-y-4 animate-fade-in" id="tab-wishlist-display">
                    
                    <div className="flex items-center justify-between border-b border-white/5 pb-3">
                      <div>
                        <h2 className="text-xl md:text-2xl font-serif font-medium tracking-tight text-white flex items-center gap-2">
                          <Heart className="w-5 h-5 text-amber-500 fill-current" />
                          Избранные треки
                        </h2>
                        <p className="text-xs text-white/40 mt-1">
                          Быстрый список ваших любимых композиций для мгновенного воспроизведения.
                        </p>
                      </div>
                      <span className="text-xs font-mono font-bold text-amber-550 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-xl">
                        ★ {wishlist.length} в избранном
                      </span>
                    </div>

                    {wishlist.length === 0 ? (
                      <div className="bg-transparent border border-white/5 border-dashed rounded-3xl p-12 text-center flex flex-col items-center justify-center gap-3">
                        <FolderHeart className="w-10 h-10 text-white/10" />
                        <h3 className="font-bold text-sm text-zinc-350">Список избранного пуст</h3>
                        <p className="text-white/30 text-xs max-w-sm">
                          Нажимайте на звездочку (☆) во время прослушивания песен, чтобы добавить их в свой список избранного.
                        </p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        {wishlist.map((track, i) => {
                          const isActive = currentTrack?.id === track.id || currentTrack?.deezer_id === track.deezer_id;
                          const isDownloaded = library.some(l => l.deezer_id === track.deezer_id);
                          const isDownloading = !!downloadingIds[track.deezer_id];

                          return (
                            <TrackRow 
                              key={track.id}
                              id={track.id}
                              title={track.title}
                              artist={track.artist}
                              deezerId={track.deezer_id}
                              albumCover={track.album_art}
                              previewUrl={track.preview_url}
                              index={i}
                              isActive={isActive}
                              isPlaying={isPlaying}
                              isDownloaded={isDownloaded}
                              isDownloading={isDownloading}
                              isWishlisted={true}
                              onPlay={() => handlePlaySong(track, wishlist)}
                              onWishlistToggle={() => handleWishlistToggle({ id: track.deezer_id, title: track.title, artist: track.artist, album_art: track.album_art, preview_url: track.preview_url })}
                              onDownload={() => handleDownloadTrack({ id: track.deezer_id, title: track.title, artist: track.artist, album: { cover_medium: track.album_art }, preview: track.preview_url })}
                            />
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* 4. RADIO BROWSER */}
                {activeTab === "radio" && (
                  <div className="space-y-4 animate-fade-in" id="tab-radio-display">
                    
                    <div className="bg-gradient-to-r from-amber-955/20 via-[#0a0a0a] to-[#0c0c0c] border border-white/5 p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <h2 className="text-lg md:text-xl font-serif font-medium text-amber-500 flex items-center gap-2">
                          <Radio className="w-5 h-5" />
                          Мир стримингового Интернет-Радио
                        </h2>
                        <p className="text-xs text-white/40 mt-1">
                          Бесплатный доступ к более чем 30 000 мировых радиостанций. Ищите по жанрам или городам.
                        </p>
                      </div>

                      {/* Filter Search mode select */}
                      <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
                        <span className="text-xs text-white/30">Искать по:</span>
                        <select 
                          value={radioSearchMode}
                          onChange={(e) => setRadioSearchMode(e.target.value as any)}
                          className="bg-zinc-950 border border-white/10 text-zinc-300 text-xs font-semibold px-2 py-1.5 rounded-lg focus:outline-none cursor-pointer"
                        >
                          <option value="byname">Названию</option>
                          <option value="bytag">Тегу (Жанру)</option>
                          <option value="bycountry">Стране</option>
                        </select>
                        <button 
                          onClick={() => { setSearchQuery(""); fetchPopularRadio(); }}
                          className="bg-white/5 border border-white/10 hover:bg-white/10 text-zinc-100 text-xs font-bold px-3 py-1.5 rounded-lg active:scale-95 transition-all"
                        >
                          Популярные
                        </button>
                      </div>
                    </div>

                    {/* Radio Grid layout */}
                    <div className="space-y-2">
                      <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-wider mb-1">Радиостанции</h3>
                      
                      {radioStations.length === 0 ? (
                        <div className="h-52 flex items-center justify-center text-zinc-500 text-sm">
                          Пусто или радиосервис временно недоступен.
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {radioStations.map((station, i) => {
                            const isActive = currentTrack?.id === station.stationuuid;
                            return (
                              <RadioRow 
                                key={station.stationuuid}
                                station={station}
                                index={i}
                                isActive={isActive}
                                isPlaying={isPlaying}
                                onPlayToggle={() => {
                                  if (isActive) {
                                    setIsPlaying(!isPlaying);
                                  } else {
                                    handlePlayRadio(station);
                                  }
                                }}
                              />
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 5. ARTIST DETAILED CART PROFILE PAGE */}
                {activeTab === "artist" && selectedArtist && (
                  <div className="space-y-6 animate-fade-in" id="tab-artist-detail-display">
                    
                    {/* Header banner */}
                    <div className="bg-gradient-to-r from-amber-955/20 via-[#0a0a0a] to-[#0c0c0c] p-6 md:p-8 rounded-3xl border border-white/5 flex flex-col md:flex-row items-center gap-6 shadow-2xl relative overflow-hidden">
                      <button 
                        onClick={() => handleToggleTab("charts")}
                        className="absolute top-4 left-4 p-2 bg-black/40 hover:bg-black/80 rounded-xl text-zinc-400 hover:text-white transition-all text-xs font-bold flex items-center gap-1 cursor-pointer"
                      >
                        <ArrowLeft className="w-4 h-4" /> Назад
                      </button>

                      <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden border-2 border-amber-500 shadow-lg flex-shrink-0 bg-zinc-800">
                        {artistInfo?.picture_big ? (
                          <img 
                            src={artistInfo.picture_big} 
                            alt={selectedArtist.name} 
                            referrerPolicy="no-referrer"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Users className="w-12 h-12 text-zinc-600 m-auto" />
                        )}
                      </div>

                      <div className="text-center md:text-left space-y-2 mt-4 md:mt-0">
                        <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest font-mono">
                          Карточка исполнителя
                        </span>
                        <h2 className="text-2xl md:text-4xl font-serif font-medium text-white leading-none">
                          {selectedArtist.name}
                        </h2>
                        {artistInfo?.nb_fan ? (
                          <p className="text-xs text-white/40">
                            Количество поклонников: <strong className="text-zinc-200 font-bold">{Number(artistInfo.nb_fan).toLocaleString()}</strong>
                          </p>
                        ) : null}
                        {artistInfo?.nb_album ? (
                          <p className="text-[11px] text-[#555] uppercase tracking-widest font-mono">
                            Альбомов в базе: {artistInfo.nb_album}
                          </p>
                        ) : null}
                      </div>
                    </div>

                    {/* Left & Right layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      
                      {/* Top songs (Cols: 2) */}
                      <div className="lg:col-span-2 space-y-3">
                        <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">Самые популярные треки</h3>
                        <div className="space-y-2">
                          {artistTracks.length === 0 ? (
                            <p className="text-zinc-500 text-sm">Нет доступных треков.</p>
                          ) : (
                            artistTracks.map((track, i) => {
                              const isActive = currentTrack?.id === track.id;
                              const isDownloaded = library.some(l => l.deezer_id === track.id);
                              const isDownloading = !!downloadingIds[track.id];
                              const isWishlisted = wishlist.some(w => w.deezer_id === track.id);

                              return (
                                <TrackRow 
                                  key={track.id}
                                  id={track.id}
                                  title={track.title}
                                  artist={selectedArtist.name}
                                  deezerId={track.id}
                                  albumCover={track.album?.cover_medium}
                                  albumTitle={track.album?.title}
                                  previewUrl={track.preview}
                                  index={i}
                                  isActive={isActive}
                                  isPlaying={isPlaying}
                                  isDownloaded={isDownloaded}
                                  isDownloading={isDownloading}
                                  isWishlisted={isWishlisted}
                                  onPlay={() => handlePlaySong(track, artistTracks)}
                                  onWishlistToggle={() => handleWishlistToggle(track)}
                                  onDownload={() => handleDownloadTrack(track)}
                                />
                              );
                            })
                          )}
                        </div>
                      </div>

                      {/* Related Artists list (Cols: 1) */}
                      <div className="space-y-3">
                        <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">Похожие исполнители</h3>
                        <div className="space-y-2 bg-[#0a0a0a] border border-white/5 p-4 rounded-2xl block">
                          {artistRelated.length === 0 ? (
                            <p className="text-zinc-600 text-xs p-2 text-center">Похожих исполнителей не обнаружено.</p>
                          ) : (
                            artistRelated.map((related, idx) => (
                              <button
                                key={related.id}
                                onClick={() => handleSelectArtist(related.id, related.name)}
                                className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 text-left transition-all group"
                              >
                                <img 
                                  src={related.picture_medium || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80"} 
                                  alt={related.name}
                                  referrerPolicy="no-referrer"
                                  className="w-10 h-10 rounded-full object-cover border border-white/10"
                                />
                                <div className="min-w-0 flex-1">
                                  <h4 className="text-sm font-semibold text-zinc-200 group-hover:text-amber-500 truncate">
                                    {related.name}
                                  </h4>
                                  {related.nb_fan ? (
                                    <p className="text-[10px] text-zinc-500 font-mono">
                                      {Number(related.nb_fan).toLocaleString()} фанатов
                                    </p>
                                  ) : null}
                                </div>
                              </button>
                            ))
                          )}
                        </div>
                      </div>

                    </div>
                  </div>
                )}

              </>
            )}

          </div>

          {/* ──── BOT PERSISTENT AUDIO CONTROLLER CARD ──── */}
          <AudioPlayer 
            currentTrack={currentTrack}
            isPlaying={isPlaying}
            onPlayPauseToggle={setIsPlaying}
            onNext={handleNextTrack}
            onPrev={handlePrevTrack}
          />

        </main>
      </div>

      {/* ──── MOBILE SIDEBAR NAV DRAWER OVERLAY ──── */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex animate-fade-in">
          <div className="w-[280px] bg-[#070707] p-6 flex flex-col justify-between shadow-2xl border-r border-white/5 relative animate-[slide-in-right_0.3s_ease]">
            <button 
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 right-4 p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-8">
              {/* Profile logo info */}
              <div className="flex items-center gap-3 mt-4 select-none">
                <Music className="w-7 h-7 text-amber-500" />
                <div>
                  <h1 className="font-serif italic font-bold text-lg text-amber-500">FastMusic</h1>
                  <p className="text-[10px] text-zinc-500">Музыкальный Веб-Плеер</p>
                </div>
              </div>

              {/* Mobile tabs buttons links */}
              <div className="space-y-1">
                <button
                  onClick={() => handleToggleTab("charts")}
                  className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-semibold flex items-center gap-3 transition-colors ${
                    activeTab === "charts" ? "bg-amber-600 text-white" : "text-zinc-400 hover:bg-white/5"
                  }`}
                >
                  <Flame className="w-4 h-4" /> Чарты и новинки
                </button>
                <button
                  onClick={() => handleToggleTab("library")}
                  className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-semibold flex items-center gap-3 transition-colors ${
                    activeTab === "library" ? "bg-amber-600 text-white" : "text-zinc-400 hover:bg-white/5"
                  }`}
                >
                  <Library className="w-4 h-4" /> Мои аудио (MP3) ({library.length})
                </button>
                <button
                  onClick={() => handleToggleTab("wishlist")}
                  className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-semibold flex items-center gap-3 transition-colors ${
                    activeTab === "wishlist" ? "bg-amber-600 text-white" : "text-zinc-400 hover:bg-white/5"
                  }`}
                >
                  <Heart className="w-4 h-4" /> Избранное (★ {wishlist.length})
                </button>
                <button
                  onClick={() => handleToggleTab("radio")}
                  className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-semibold flex items-center gap-3 transition-colors ${
                    activeTab === "radio" ? "bg-amber-600 text-white" : "text-zinc-400 hover:bg-white/5"
                  }`}
                >
                  <Radio className="w-4 h-4" /> Интернет-Радио
                </button>
              </div>
            </div>

            <div className="text-xs text-[#555] text-center border-t border-white/5 p-4 font-mono">
              ВЕРСИЯ 1.2 • MAGDEVICE
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
