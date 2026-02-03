import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Clock, AlertTriangle, Youtube, Filter, Server, ArrowRight } from 'lucide-react';
import Navbar from './Navbar';
import SearchModal from './SearchModal';
import MovieCard from './MovieCard';
import MovieDetailsModal from './MovieDetailsModal';
import '../styles/HomePage.css';
import '../styles/MoviesPage.css';
import MobileToggle from './MobileToggle';

const MoviesPage = () => {
    const [movies, setMovies] = useState([]);
    const [filteredMovies, setFilteredMovies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [filter, setFilter] = useState('all');
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [stats, setStats] = useState({ total: 0, available: 0, pending: 0, youtube: 0 });
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCatalog = async (isBackground = false) => {
            try {
                if (!isBackground) {
                    setLoading(true);
                    setError(null);
                }
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
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                console.error("Failed to fetch catalog", error);
                if (!isBackground) {
                    setError("Backend offline");
                }
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
            
            <div style={{ marginTop: '110px', display: 'flex', justifyContent: 'center', position: 'relative', zIndex: 10 }}>
                <MobileToggle />
            </div>

            <div className="content-container catalog-container" style={{ paddingTop: '20px' }}>
                <div className="catalog-header">
                    <h1 className="row-title">CATÁLOGO COMPLETO</h1>
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
                     <div className="row-empty" style={{ 
                         padding: '60px 20px', 
                         textAlign: 'center',
                         maxWidth: '600px',
                         margin: '0 auto'
                     }}>
                        {error ? (
                            <>
                                <Server size={48} style={{ opacity: 0.5, marginBottom: '16px', color: '#e50914' }} />
                                <h3 style={{ marginBottom: '12px' }}>Servidor Offline</h3>
                                <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: '1.6' }}>
                                    O backend não está respondendo.<br/>
                                    Para ver os filmes, rode o servidor localmente:
                                </p>
                                <div style={{ 
                                    background: 'rgba(255,255,255,0.05)', 
                                    padding: '20px', 
                                    borderRadius: '8px',
                                    textAlign: 'left',
                                    marginBottom: '24px',
                                    fontFamily: 'monospace',
                                    fontSize: '0.9rem'
                                }}>
                                    <p style={{ margin: '0 0 8px 0', color: '#888' }}># No Windows:</p>
                                    <p style={{ margin: '0 0 16px 0' }}>start-local.bat</p>
                                    <p style={{ margin: '0 0 8px 0', color: '#888' }}># No Mac/Linux:</p>
                                    <p style={{ margin: 0 }}>./start-local.sh</p>
                                </div>
                                <p style={{ fontSize: '0.85rem', color: '#666' }}>
                                    Ou veja o arquivo <code>SETUP_LOCAL.md</code> para instruções completas.
                                </p>
                            </>
                        ) : (
                            <>
                                <AlertTriangle size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                                Nenhum filme encontrado no catálogo.
                            </>
                        )}
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
