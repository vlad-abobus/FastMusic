import express from "express";
import path from "path";
import fs from "fs";
import { createServer as createViteServer } from "vite";

// ──── DATABASE & STORAGE CONFIGURATION ────
const DATA_DIR = path.resolve(process.cwd(), "data");
const DOWNLOADS_DIR = path.resolve(process.cwd(), "downloads");
const LIBRARY_FILE = path.join(DATA_DIR, "library.json");
const WISHLIST_FILE = path.join(DATA_DIR, "wishlist.json");

// Ensure directories exist
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}
if (!fs.existsSync(DOWNLOADS_DIR)) {
  fs.mkdirSync(DOWNLOADS_DIR, { recursive: true });
}

// Ensure database files exist
if (!fs.existsSync(LIBRARY_FILE)) {
  fs.writeFileSync(LIBRARY_FILE, JSON.stringify([], null, 2));
}
if (!fs.existsSync(WISHLIST_FILE)) {
  fs.writeFileSync(WISHLIST_FILE, JSON.stringify([], null, 2));
}

// Helpers to read/write databases safely
interface Track {
  id: string; // unique UUID or timestamp-based ID
  title: string;
  artist: string;
  album_art: string;
  file_path: string;
  deezer_id?: number;
  preview_url?: string;
  duration?: number;
}

interface WishlistItem {
  id: string;
  title: string;
  artist: string;
  album_art: string;
  preview_url: string;
  deezer_id: number;
}

function readLibrary(): Track[] {
  try {
    const data = fs.readFileSync(LIBRARY_FILE, "utf-8");
    return JSON.parse(data) as Track[];
  } catch (e) {
    console.error("Error reading library file:", e);
    return [];
  }
}

function writeLibrary(data: Track[]) {
  try {
    fs.writeFileSync(LIBRARY_FILE, JSON.stringify(data, null, 2), "utf-8");
  } catch (e) {
    console.error("Error writing library file:", e);
  }
}

function readWishlist(): WishlistItem[] {
  try {
    const data = fs.readFileSync(WISHLIST_FILE, "utf-8");
    return JSON.parse(data) as WishlistItem[];
  } catch (e) {
    console.error("Error reading wishlist file:", e);
    return [];
  }
}

function writeWishlist(data: WishlistItem[]) {
  try {
    fs.writeFileSync(WISHLIST_FILE, JSON.stringify(data, null, 2), "utf-8");
  } catch (e) {
    console.error("Error writing wishlist file:", e);
  }
}

// ──── EXPRESS WEB SERVER SETUP ────
async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // ──── API ROUTES ────

  // 1. Health check
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", app: "FastMusic Backend" });
  });

  // 2. Deezer: Search Proxy (to avoid CORS)
  app.get("/api/deezer/search", async (req, res) => {
    const { q, type } = req.query;
    if (!q) {
      return res.status(400).json({ error: "Missing query parameter 'q'" });
    }

    try {
      let url = `https://api.deezer.com/search?q=${encodeURIComponent(String(q))}&limit=30`;
      if (type === "albums") {
        url = `https://api.deezer.com/search/album?q=${encodeURIComponent(String(q))}&limit=20`;
      } else if (type === "artists") {
        url = `https://api.deezer.com/search/artist?q=${encodeURIComponent(String(q))}&limit=20`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Deezer API responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer search error:", error.message);
      res.status(500).json({ error: "Failed to fetch search results from Deezer" });
    }
  });

  // 3. Deezer: Charts Proxy
  app.get("/api/deezer/charts", async (req, res) => {
    try {
      const response = await fetch("https://api.deezer.com/chart/0/tracks?limit=30");
      if (!response.ok) {
        throw new Error(`Deezer API responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer charts error:", error.message);
      res.status(500).json({ error: "Failed to fetch charts from Deezer" });
    }
  });

  // 4. Deezer: Artist Top Tracks & Related
  app.get("/api/deezer/artist/:id/top", async (req, res) => {
    const { id } = req.params;
    try {
      const response = await fetch(`https://api.deezer.com/artist/${id}/top?limit=15`);
      if (!response.ok) {
        throw new Error(`Deezer artist top tracks responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer artist top error:", error.message);
      res.status(500).json({ error: "Failed to fetch top tracks for artist" });
    }
  });

  app.get("/api/deezer/artist/:id/related", async (req, res) => {
    const { id } = req.params;
    try {
      const response = await fetch(`https://api.deezer.com/artist/${id}/related?limit=15`);
      if (!response.ok) {
        throw new Error(`Deezer artist related responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer related error:", error.message);
      res.status(500).json({ error: "Failed to fetch related artists" });
    }
  });

  app.get("/api/deezer/artist/:id", async (req, res) => {
    const { id } = req.params;
    try {
      const response = await fetch(`https://api.deezer.com/artist/${id}`);
      if (!response.ok) {
        throw new Error(`Deezer artist details responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer artist details error:", error.message);
      res.status(500).json({ error: "Failed to fetch artist details" });
    }
  });

  // 5. Deezer: Album details
  app.get("/api/deezer/album/:id", async (req, res) => {
    const { id } = req.params;
    try {
      const response = await fetch(`https://api.deezer.com/album/${id}`);
      if (!response.ok) {
        throw new Error(`Deezer album details responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Deezer album details error:", error.message);
      res.status(500).json({ error: "Failed to fetch album details" });
    }
  });

  // 6. Radio Browser: Popular stations
  app.get("/api/radio/popular", async (req, res) => {
    try {
      // Use de1 or check general DNS, radio-browser.info list of IPs
      const response = await fetch(
        "https://de1.api.radio-browser.info/json/stations/topclick/30"
      );
      if (!response.ok) {
        throw new Error(`Radio Browser API responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Radio popular error:", error.message);
      // Fallback with standard mirror if de1 is slow/unreachable
      try {
        const fallbackRes = await fetch(
          "https://at1.api.radio-browser.info/json/stations/topclick/30"
        );
        const data = await fallbackRes.json();
        return res.json(data);
      } catch (fbErr: any) {
        res.status(500).json({ error: "Failed to load popular radio stations" });
      }
    }
  });

  // 7. Radio Browser: Search (by Name, Tag, Country)
  app.get("/api/radio/search", async (req, res) => {
    const { q, mode } = req.query;
    if (!q) {
      return res.status(400).json({ error: "Missing radio search query 'q'" });
    }
    const cleanMode = String(mode || "byname"); // byname, bytag, bycountry
    try {
      const response = await fetch(
        `https://de1.api.radio-browser.info/json/stations/${cleanMode}/${encodeURIComponent(
          String(q)
        )}?limit=30`
      );
      if (!response.ok) {
        throw new Error(`Radio Browser Search responded with status ${response.status}`);
      }
      const data = await response.json();
      res.json(data);
    } catch (error: any) {
      console.error("Radio search error:", error.message);
      res.status(500).json({ error: "Failed to search radio stations" });
    }
  });

  // 8. Library downloads: List all tracks
  app.get("/api/library", (req, res) => {
    const list = readLibrary();
    // Validate if file physically exists. If not, auto-clean (like logic.py)
    const validatedList = list.filter((track) => {
      if (fs.existsSync(track.file_path)) {
        return true;
      }
      return false; // exclude if deleted on disk
    });

    if (validatedList.length !== list.length) {
      writeLibrary(validatedList);
    }
    res.json(validatedList);
  });

  // 9. Library downloads: Save a track (Simulate download from preview URL)
  app.post("/api/library/download", async (req, res) => {
    const { title, artist, album_art, preview_url, deezer_id } = req.body;
    if (!title || !artist) {
      return res.status(400).json({ error: "Missing title or artist metadata" });
    }

    const cleanArtist = artist.replace(/[/\\?%*:|"<>]/g, "");
    const cleanTitle = title.replace(/[/\\?%*:|"<>]/g, "");
    const fileName = `${cleanArtist} - ${cleanTitle}.mp3`;
    const targetPath = path.join(DOWNLOADS_DIR, fileName);

    const library = readLibrary();

    // Check if already in library
    const existing = library.find(
      (t) =>
        t.artist.toLowerCase() === artist.toLowerCase() &&
        t.title.toLowerCase() === title.toLowerCase()
    );
    if (existing && fs.existsSync(existing.file_path)) {
      return res.json({ message: "Track already downloaded", track: existing });
    }

    try {
      // In the browser/sandbox context, caching the 30-second preview stream is extremely fast,
      // reliable, produces perfect high quality MP3 streams directly, and respects user's download action.
      let sourceUrl = preview_url;

      // If no preview_url supplied, default to searching Deezer for it
      if (!sourceUrl && deezer_id) {
        try {
          const trackRes = await fetch(`https://api.deezer.com/track/${deezer_id}`);
          if (trackRes.ok) {
            const trackData = await trackRes.json();
            sourceUrl = trackData.preview;
          }
        } catch (_) {}
      }

      if (!sourceUrl) {
        // Search Deezer via query if still not present
        try {
          const searchRes = await fetch(
            `https://api.deezer.com/search?q=${encodeURIComponent(artist + " " + title)}`
          );
          if (searchRes.ok) {
            const searchData = await searchRes.json();
            if (searchData.data && searchData.data.length > 0) {
              sourceUrl = searchData.data[0].preview;
            }
          }
        } catch (_) {}
      }

      if (!sourceUrl) {
        return res.status(400).json({ error: "No stream or preview URL available for download" });
      }

      console.log(`Downloading track from ${sourceUrl} to ${targetPath}`);
      const audioRes = await fetch(sourceUrl);
      if (!audioRes.ok) {
        throw new Error(`Failed to fetch audio stream. HTTP status ${audioRes.status}`);
      }

      const arrayBuffer = await audioRes.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      fs.writeFileSync(targetPath, buffer);

      const newTrack: Track = {
        id: `local_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        title,
        artist,
        album_art: album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
        file_path: targetPath,
        deezer_id: Number(deezer_id) || undefined,
        preview_url: sourceUrl,
        duration: 30 // Preview MP3 is 30 seconds
      };

      library.push(newTrack);
      writeLibrary(library);

      res.status(201).json({ message: "Download successful", track: newTrack });
    } catch (err: any) {
      console.error("Download track error:", err.message);
      res.status(500).json({ error: `Failed to download: ${err.message}` });
    }
  });

  // 10. Library downloads: Stream track with HTTP Range support
  app.get("/api/library/stream/:id", (req, res) => {
    const { id } = req.params;
    const library = readLibrary();
    const track = library.find((t) => t.id === id);

    if (!track) {
      return res.status(404).json({ error: "Track not found in library" });
    }

    if (!fs.existsSync(track.file_path)) {
      return res.status(410).json({ error: "Audio file is missing from local storage" });
    }

    // Express res.sendFile automatically handles HTTP range checks out of the box
    res.sendFile(track.file_path);
  });

  // 11. Library downloads: Delete a track
  app.delete("/api/library/:id", (req, res) => {
    const { id } = req.params;
    const library = readLibrary();
    const trackIndex = library.findIndex((t) => t.id === id);

    if (trackIndex === -1) {
      return res.status(404).json({ error: "Track not found" });
    }

    const track = library[trackIndex];
    try {
      if (fs.existsSync(track.file_path)) {
        fs.unlinkSync(track.file_path);
        console.log(`Physically deleted: ${track.file_path}`);
      }
    } catch (e: any) {
      console.warn(`Filesystem delete failed, but removing database record:`, e.message);
    }

    library.splice(trackIndex, 1);
    writeLibrary(library);

    res.json({ success: true, message: "Track removed from library" });
  });

  // 12. Wishlist: List wishlist items
  app.get("/api/wishlist", (req, res) => {
    res.json(readWishlist());
  });

  // 13. Wishlist: Add to wishlist
  app.post("/api/wishlist", (req, res) => {
    const { title, artist, album_art, preview_url, deezer_id } = req.body;
    if (!title || !artist || !deezer_id) {
      return res.status(400).json({ error: "Missing required wishlist fields" });
    }

    const wishlist = readWishlist();
    const exists = wishlist.find((w) => w.deezer_id === Number(deezer_id));

    if (exists) {
      return res.json({ success: true, message: "Already in wishlist", item: exists });
    }

    const newItem: WishlistItem = {
      id: `wish_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      title,
      artist,
      album_art: album_art || "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
      preview_url: preview_url || "",
      deezer_id: Number(deezer_id)
    };

    wishlist.push(newItem);
    writeWishlist(wishlist);

    res.status(201).json({ success: true, message: "Added to wishlist", item: newItem });
  });

  // 14. Wishlist: Remove track
  app.delete("/api/wishlist/:deezer_id", (req, res) => {
    const deezerId = Number(req.params.deezer_id);
    let wishlist = readWishlist();
    const originalLength = wishlist.length;
    wishlist = wishlist.filter((w) => w.deezer_id !== deezerId);

    if (wishlist.length === originalLength) {
      return res.status(404).json({ error: "Item not found in wishlist" });
    }

    writeWishlist(wishlist);
    res.json({ success: true, message: "Removed from wishlist" });
  });

  // ──── VITE DEVELOPMENT SERVER INTERTWINING ────
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Serve static frontend files in production
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*all", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[FastMusic] Full-stack music server running on http://localhost:${PORT}`);
  });
}

startServer();
