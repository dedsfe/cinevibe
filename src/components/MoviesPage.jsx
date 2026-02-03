import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Clock, AlertTriangle, Youtube, Filter } from 'lucide-react';
import Navbar from './Navbar';
import SearchModal from './SearchModal';
import MovieCard from './MovieCard';
import MovieDetailsModal from './MovieDetailsModal';
import '../styles/HomePage.css';
import '../styles/MoviesPage.css';

const MoviesPage = () => {
    const [movies, setMovies] = useState([]);
    const [filteredMovies, setFilteredMovies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [filter, setFilter] = useState('all');
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [stats, setStats] = useState({ total: 0, available: 0, pending: 0, youtube: 0 });
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCatalog = async (isBackground = false) => {
            try {
                if (!isBackground) setLoading(true);
                const response = await fetch(`${API_BASE_URL}/catalog?limit=1000`);
                if (response.ok) {
                    const data = await response.json();
                    
                    const allMovies = data.results || [];
                    
                    // Calculate stats
                    const newStats = {
                        total: allMovies.length,
                        available: allMovies.filter(m => m.isAvailable).length,
                        pending: allMovies.filter(m => !m.embedUrl || m.embedUrl === 'NOT_FOUND').length,
                        youtube: allMovies.filter(m => m.embedUrl && m.embedUrl.includes('youtube')).length
                    };
                    setStats(newStats);
                    
                    setMovies(allMovies);
                    applyFilter(allMovies, filter);
                }
            } catch (error) {
                console.error("Failed to fetch catalog", error);
            } finally {
                if (!isBackground) setLoading(false);
            }
        };

        fetchCatalog(); // Initial load

        // Auto-refresh every 5 seconds to show new movies appearing
        const interval = setInterval(() => {
            fetchCatalog(true);
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    const applyFilter = (movieList, filterType) => {
        let filtered = movieList;
        
        switch(filterType) {
            case 'available':
                filtered = movieList.filter(m => m.isAvailable);
                break;
            case 'pending':
                filtered = movieList.filter(m => !m.embedUrl || m.embedUrl === 'NOT_FOUND');
                break;
            case 'youtube':
                filtered = movieList.filter(m => m.embedUrl && m.embedUrl.includes('youtube'));
                break;
            default:
                filtered = movieList;
        }
        
        setFilteredMovies(filtered);
    };

    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
        applyFilter(movies, newFilter);
    };

    const handleMovieClick = (movie) => {
        setSelectedMovie(movie);
    };

    const closeModal = () => {
        setSelectedMovie(null);
    };

    return (
        <div className="homepage">
            <Navbar onSearchClick={() => setIsSearchOpen(true)} />
            
            <div className="content-container catalog-container">
                <div className="catalog-header">
                    <h1 className="row-title">CATÁLOGO COMPLETO</h1>
                    
                    {/* Stats */}
                    <div className="catalog-stats">
                        <span className="stats-badge available">
                            <CheckCircle size={14} />
                            {stats.available} DISPONÍVEIS
                        </span>
                        <span className="stats-badge pending">
                            <Clock size={14} />
                            {stats.pending} PENDENTES
                        </span>
                        <span className="stats-badge">
                            TOTAL: {stats.total}
                        </span>
                    </div>
                </div>

                {/* Filter Buttons */}
                <div className="filter-container">
                    <button 
                        className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => handleFilterChange('all')}
                    >
                        <Filter size={14} />
                        TODOS ({stats.total})
                    </button>
                    <button 
                        className={`filter-chip available ${filter === 'available' ? 'active' : ''}`}
                        onClick={() => handleFilterChange('available')}
                    >
                        <CheckCircle size={14} />
                        DISPONÍVEIS ({stats.available})
                    </button>
                    <button 
                        className={`filter-chip pending ${filter === 'pending' ? 'active' : ''}`}
                        onClick={() => handleFilterChange('pending')}
                    >
                        <Clock size={14} />
                        PENDENTES ({stats.pending})
                    </button>
                    {stats.youtube > 0 && (
                        <button 
                            className={`filter-chip ${filter === 'youtube' ? 'active' : ''}`}
                            onClick={() => handleFilterChange('youtube')}
                        >
                            <AlertTriangle size={14} />
                            YOUTUBE ({stats.youtube})
                        </button>
                    )}
                </div>
                
                {loading ? (
                    <div className="row-loading">
                        <div className="loading-spinner" />
                        <span>Carregando catálogo...</span>
                    </div>
                ) : (
                    <div className="catalog-grid">
                        {(filteredMovies.length > 0 ? filteredMovies : movies).map((movie, index) => (
                           <div key={movie.id || index} className="grid-item">
                               <MovieCard 
                                    movie={movie} 
                                    index={index} 
                                    onClick={handleMovieClick}
                                    isAvailable={movie.isAvailable}
                               />
                           </div>
                        ))}
                    </div>
                )}
                
                {!loading && movies.length === 0 && (
                     <div className="row-empty">
                        Nenhum filme encontrado no catálogo.
                     </div>
                )}
            </div>

            {isSearchOpen && (
                <SearchModal 
                    onClose={() => setIsSearchOpen(false)} 
                    onMovieClick={handleMovieClick} 
                />
            )}

            <AnimatePresence>
                {selectedMovie && (
                    <MovieDetailsModal 
                        movie={selectedMovie} 
                        onClose={closeModal} 
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default MoviesPage;
