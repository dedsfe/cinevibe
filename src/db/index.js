// IndexedDB Database for Filfil
const DB_NAME = 'FilfilDB';
const DB_VERSION = 4; // Incremented to force upgrade

// Initialize IndexedDB
export const initDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Store for My List
      if (!db.objectStoreNames.contains('myList')) {
        const myListStore = db.createObjectStore('myList', { keyPath: 'id' });
        myListStore.createIndex('addedAt', 'addedAt', { unique: false });
      }
      
      // Store for API Cache
      if (!db.objectStoreNames.contains('apiCache')) {
        const cacheStore = db.createObjectStore('apiCache', { keyPath: 'endpoint' });
        cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      // Store for Movie Details (reduces API calls)
      if (!db.objectStoreNames.contains('movieDetails')) {
        db.createObjectStore('movieDetails', { keyPath: 'id' });
      }

      // Store for Persistent Video Links (Offline Playback)
      if (!db.objectStoreNames.contains('videoLinks')) {
        db.createObjectStore('videoLinks', { keyPath: 'id' });
      }
    };
  });
};

// My List Operations
export const addToMyList = async (movie) => {
  const db = await initDB();
  const transaction = db.transaction(['myList'], 'readwrite');
  const store = transaction.objectStore('myList');
  
  const item = {
    ...movie,
    addedAt: new Date().toISOString()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.put(item);
    request.onsuccess = () => {
      // Trigger background scrape
      fetch('http://127.0.0.1:8080/api/scrape-background', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: movie.title || movie.name,
          tmdbId: movie.id
        })
      }).catch(err => console.log('Background scrape trigger failed:', err));

      resolve(item);
    };
    request.onerror = () => reject(request.error);
  });
};

export const removeFromMyList = async (movieId) => {
  const db = await initDB();
  const transaction = db.transaction(['myList'], 'readwrite');
  const store = transaction.objectStore('myList');
  
  return new Promise((resolve, reject) => {
    const request = store.delete(movieId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

export const getMyList = async () => {
  const db = await initDB();
  const transaction = db.transaction(['myList'], 'readonly');
  const store = transaction.objectStore('myList');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => {
      const items = request.result.sort((a, b) => 
        new Date(b.addedAt) - new Date(a.addedAt)
      );
      resolve(items);
    };
    request.onerror = () => reject(request.error);
  });
};

export const isInMyList = async (movieId) => {
  const db = await initDB();
  const transaction = db.transaction(['myList'], 'readonly');
  const store = transaction.objectStore('myList');
  
  return new Promise((resolve, reject) => {
    const request = store.get(movieId);
    request.onsuccess = () => resolve(!!request.result);
    request.onerror = () => reject(request.error);
  });
};

// API Cache Operations
const CACHE_DURATION = 60 * 60 * 1000; // 1 hour in milliseconds

export const getCachedData = async (endpoint) => {
  const db = await initDB();
  const transaction = db.transaction(['apiCache'], 'readonly');
  const store = transaction.objectStore('apiCache');
  
  return new Promise((resolve, reject) => {
    const request = store.get(endpoint);
    request.onsuccess = () => {
      const cached = request.result;
      if (cached) {
        const age = Date.now() - cached.timestamp;
        if (age < CACHE_DURATION) {
          resolve(cached.data);
          return;
        }
      }
      resolve(null);
    };
    request.onerror = () => reject(request.error);
  });
};

export const setCachedData = async (endpoint, data) => {
  const db = await initDB();
  const transaction = db.transaction(['apiCache'], 'readwrite');
  const store = transaction.objectStore('apiCache');
  
  const cacheEntry = {
    endpoint,
    data,
    timestamp: Date.now()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.put(cacheEntry);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// Clear old cache entries
export const clearOldCache = async () => {
  const db = await initDB();
  const transaction = db.transaction(['apiCache'], 'readwrite');
  const store = transaction.objectStore('apiCache');
  const index = store.index('timestamp');
  
  const cutoff = Date.now() - CACHE_DURATION;
  
  return new Promise((resolve, reject) => {
    const request = index.openCursor();
    
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        if (cursor.value.timestamp < cutoff) {
          cursor.delete();
        }
        cursor.continue();
      } else {
        resolve();
      }
    };
    
    request.onerror = () => reject(request.error);
  });
};

// Movie Details Cache (for trailers, providers, etc.)
export const getCachedMovieDetails = async (movieId) => {
  const db = await initDB();
  const transaction = db.transaction(['movieDetails'], 'readonly');
  const store = transaction.objectStore('movieDetails');
  
  return new Promise((resolve, reject) => {
    const request = store.get(movieId);
    request.onsuccess = () => {
      const cached = request.result;
      if (cached) {
        const age = Date.now() - cached.timestamp;
        if (age < CACHE_DURATION) {
          resolve(cached.data);
          return;
        }
      }
      resolve(null);
    };
    request.onerror = () => reject(request.error);
  });
};

export const setCachedMovieDetails = async (movieId, data) => {
  const db = await initDB();
  const transaction = db.transaction(['movieDetails'], 'readwrite');
  const store = transaction.objectStore('movieDetails');
  
  const cacheEntry = {
    id: movieId,
    data,
    timestamp: Date.now()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.put(cacheEntry);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// Video Link Persistence (Permanent / Long-term)
export const getVideoLink = async (tmdbId) => {
  const db = await initDB();
  const transaction = db.transaction(['videoLinks'], 'readonly');
  const store = transaction.objectStore('videoLinks');
  
  return new Promise((resolve, reject) => {
    const request = store.get(String(tmdbId));
    request.onsuccess = () => resolve(request.result?.url || null);
    request.onerror = () => reject(request.error);
  });
};

export const saveVideoLink = async (tmdbId, url) => {
  const db = await initDB();
  const transaction = db.transaction(['videoLinks'], 'readwrite');
  const store = transaction.objectStore('videoLinks');
  
  const item = {
    id: String(tmdbId),
    url,
    savedAt: Date.now()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.put(item);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};