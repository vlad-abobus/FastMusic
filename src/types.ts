export interface DeezerTrack {
  id: number;
  title: string;
  duration: number;
  preview: string;
  artist: {
    id: number;
    name: string;
    picture_small?: string;
    picture_medium?: string;
  };
  album: {
    id: number;
    title: string;
    cover_small?: string;
    cover_medium?: string;
    cover_big?: string;
  };
}

export interface DeezerAlbum {
  id: number;
  title: string;
  cover_medium: string;
  cover_small: string;
  nb_tracks?: number;
  tracks_count?: number;
  artist?: string | { name: string };
  release_date?: string;
}

export interface DeezerArtist {
  id: number;
  name: string;
  picture_medium: string;
  picture_big: string;
  nb_fan?: number;
  nb_fans?: number;
  nb_album?: number;
  nb_albums?: number;
}

export interface LocalTrack {
  id: string;
  title: string;
  artist: string;
  album_art: string;
  file_path: string;
  deezer_id?: number;
  preview_url?: string;
  duration?: number;
}

export interface WishlistTrack {
  id: string;
  title: string;
  artist: string;
  album_art: string;
  preview_url: string;
  deezer_id: number;
}

export interface RadioStation {
  stationuuid: string;
  name: string;
  url: string;
  url_resolved?: string;
  favicon: string;
  tags?: string;
  country?: string;
  bitrate?: number;
  language?: string;
}

export type ActiveTab = "charts" | "library" | "wishlist" | "radio" | "artist" | "album";
export type SearchFilter = "all" | "tracks" | "albums" | "artists";

export interface PlaybackItem {
  id: string | number;
  title: string;
  artist: string;
  album_art: string;
  url: string; // can be preview, stream, or radio url
  isRadio?: boolean;
  deezer_id?: number;
  localId?: string; // set if it's a downloaded file
}
