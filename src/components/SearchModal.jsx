import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, X } from 'lucide-react';
import { useTMDB, getPosterUrl } from '../hooks/useTMDB';
import '../styles/HomePage.css'; // Reusing existing styles

const SearchModal = ({ onClose, onMovieClick }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [availability, setAvailability] = useState({});
  const { fetchData } = useTMDB();
  const inputRef = useRef(null);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
    // Prevent background scrolling
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!query.trim()) {
        setResults([]);
        return;
      }

      setIsSearching(true);
      try {
        // Search exclusively in local database
        const response = await fetch(`${API_BASE_URL}/api/movies/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data?.results) {
          setResults(data.results);
          // Local results are always available
          const availMap = {};
          data.results.forEach(m => availMap[m.id] = true);
          setAvailability(availMap);
        }
      } catch (error) {
        console.error("Search failed", error);
      } finally {
        setIsSearching(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <motion.div 
      className="search-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div 
        className="search-modal-container"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="search-modal-header">
          <Search className="search-modal-icon" size={24} />
          <input
            ref={inputRef}
            type="text"
            className="search-modal-input"
            placeholder="O que você quer assistir?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="search-modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="search-modal-results">
          {isSearching ? (
            <div className="search-modal-loading">
              <Loader2 className="spin" size={32} />
            </div>
          ) : results.length > 0 ? (
            <div className="search-results-list">
              {results.map(movie => (
                <div 
                  key={movie.id} 
                  className="search-result-item"
                  onClick={() => {
                    onMovieClick(movie);
                    onClose();
                  }}
                >
                  <img 
                    src={getPosterUrl(movie.poster_path)} 
                    alt={movie.title} 
                    className="search-result-poster"
                  />
                    <div className="search-result-info">
                    <h4>{movie.title}</h4>
                    <span className="search-result-year">
                      {(movie.release_date || '').substring(0, 4)}
                    </span>
                    <span className="search-result-badge">⚡️ Disponível</span>
                  </div>
                </div>
              ))}
            </div>
          ) : query ? (
            <div className="search-modal-empty">Nenhum resultado encontrado</div>
          ) : (
            <div className="search-modal-empty">Digite para buscar...</div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SearchModal;
