import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader2, Info } from 'lucide-react';
import { useTMDB } from '../hooks/useTMDB';
import MovieCard from './MovieCard';
import '../styles/SearchPage.css';

// Debounce helper
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
};

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [availability, setAvailability] = useState({});
  const [isSearching, setIsSearching] = useState(false);
  const { fetchData } = useTMDB();
  const navigate = useNavigate();
  
  const debouncedQuery = useDebounce(query, 500);

  // Check availability with local backend
  const checkAvailability = async (movies) => {
    if (!movies?.length) return;
    try {
      const tmdbIds = movies.map(m => m.id);
      const response = await fetch('http://127.0.0.1:3000/api/cache/check-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tmdb_ids: tmdbIds }),
      });
      if (response.ok) {
        const data = await response.json();
        setAvailability(prev => ({ ...prev, ...data }));
      }
    } catch (err) {
      console.error("Failed to check availability", err);
    }
  };

  useEffect(() => {
    const searchMovies = async () => {
      if (!debouncedQuery.trim()) {
        setResults([]);
        return;
      }

      setIsSearching(true);
      try {
        const data = await fetchData(`/search/movie?query=${encodeURIComponent(debouncedQuery)}`);
        if (data && data.results) {
          // Filter out results without poster or backdrop to keep quality high? Optional.
          const validResults = data.results.filter(m => m.poster_path);
          setResults(validResults);
          checkAvailability(validResults);
        }
      } catch (error) {
        console.error("Search failed", error);
      } finally {
        setIsSearching(false);
      }
    };

    searchMovies();
  }, [debouncedQuery, fetchData]);

  const handleMovieClick = (movie) => {
    // Navigate to watch if available, otherwise maybe show info?
    // Consistently navigate to watch page, it handles "availability" check logic too mostly
    navigate(`/watch/${movie.id}`);
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <div className="search-bar-container">
          <Search className="search-icon" size={24} />
          <input
            type="text"
            className="search-input"
            placeholder="Search for movies..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>
      </div>

      <div className="search-results-container">
        {isSearching ? (
          <div className="search-loading">
            <Loader2 className="loading-spinner" size={40} />
            <p>Searching catalog...</p>
          </div>
        ) : results.length > 0 ? (
          <>
            <h2 className="results-header">Results for "{debouncedQuery}"</h2>
            <div className="movies-grid">
              {results.map((movie, index) => (
                <MovieCard
                  key={movie.id}
                  movie={movie}
                  index={index}
                  onClick={handleMovieClick}
                  isAvailable={availability[movie.id]}
                />
              ))}
            </div>
          </>
        ) : debouncedQuery ? (
          <div className="search-empty">
            <p>No movies found for "{debouncedQuery}"</p>
          </div>
        ) : (
          <div className="search-empty">
            <p>Start typing to search for movies</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
