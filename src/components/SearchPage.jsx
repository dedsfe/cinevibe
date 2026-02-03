import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../config';
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
  const [isSearching, setIsSearching] = useState(false);
  const { fetchData } = useTMDB();
  const navigate = useNavigate();
  
  const debouncedQuery = useDebounce(query, 500);


  useEffect(() => {
    const searchMovies = async () => {
      if (!debouncedQuery.trim()) {
        setResults([]);
        return;
      }

      setIsSearching(true);
      try {
        const data = await fetchData(`/api/search/all?q=${encodeURIComponent(debouncedQuery)}`);
        if (data && data.results) {
          setResults(data.results);
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
