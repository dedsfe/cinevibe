import { API_BASE_URL } from '../config';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Tv, Filter, Search } from 'lucide-react';
import Navbar from './Navbar';
import SearchModal from './SearchModal';
import MovieCard from './MovieCard';
import MovieDetailsModal from './MovieDetailsModal';
import '../styles/HomePage.css';
import '../styles/MoviesPage.css';

const SeriesPage = () => {
    const [series, setSeries] = useState([]);
    const [filteredSeries, setFilteredSeries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [filter, setFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSeries, setSelectedSeries] = useState(null);
    const [stats, setStats] = useState({ total: 0 });
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        console.log("[SeriesPage] Component mounted");
        // Global error handler for debugging
        window.addEventListener('error', (e) => {
            console.error('[SeriesPage] Global error:', e.message);
        });
        fetchSeries();
    }, []);
    
    // Debug: mostrar estado atual
    useEffect(() => {
        console.log("[SeriesPage] State update - series:", series.length, "filtered:", filteredSeries.length, "loading:", loading, "error:", error);
    }, [series, filteredSeries, loading, error]);

    const fetchSeries = async () => {
        try {
            setLoading(true);
            console.log("[SeriesPage] Fetching series...");
            const response = await fetch(`${API_BASE_URL}/series?limit=1000`);
            console.log("[SeriesPage] Response status:", response.status);
            if (response.ok) {
                const data = await response.json();
                console.log("[SeriesPage] Data received:", data);
                const allSeries = (data.results || []).map(s => ({
                    ...s,
                    media_type: 'tv',
                    isLocalSeries: true
                }));
                
                console.log("[SeriesPage] Total series:", allSeries.length);
                setStats({ total: data.total || allSeries.length });
                setSeries(allSeries);
                setFilteredSeries(allSeries);
            } else {
                console.error("[SeriesPage] Response not OK:", response.statusText);
            }
        } catch (error) {
            console.error("[SeriesPage] Failed to fetch series:", error);
            setError("Erro ao carregar séries. Verifique se o backend está rodando.");
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async (query) => {
        setSearchQuery(query);
        
        if (!query.trim()) {
            setFilteredSeries(series);
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/series/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                const searchResults = (data.results || []).map(s => ({
                    ...s,
                    media_type: 'tv',
                    isLocalSeries: true
                }));
                setFilteredSeries(searchResults);
            }
        } catch (error) {
            console.error("Failed to search series", error);
            // Fallback: filter locally
            const filtered = series.filter(s => 
                s.title.toLowerCase().includes(query.toLowerCase())
            );
            setFilteredSeries(filtered);
        }
    };

    const handleSeriesClick = (series) => {
        setSelectedSeries(series);
    };

    const closeModal = () => {
        setSelectedSeries(null);
    };

    return (
        <div className="homepage">
            <Navbar onSearchClick={() => setIsSearchOpen(true)} />
            
            <div className="content-container catalog-container">
                <div className="catalog-header">
                    <h1 className="row-title">
                        <Tv size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
                        SÉRIES
                    </h1>
                    
                    {/* Stats */}
                    <div className="catalog-stats">
                        <span className="stats-badge available">
                            <Tv size={14} />
                            {stats.total} SÉRIES
                        </span>
                        <span className="stats-badge">
                            CARREGADAS: {series.length}
                        </span>
                        <span className="stats-badge">
                            FILTRADAS: {filteredSeries.length}
                        </span>
                    </div>
                </div>

                {/* Debug refresh button */}
                <div style={{ marginBottom: '16px' }}>
                    <button 
                        onClick={fetchSeries}
                        className="filter-chip"
                        disabled={loading}
                    >
                        {loading ? 'Carregando...' : '🔄 Recarregar Séries'}
                    </button>
                </div>

                {/* Search Bar */}
                <div className="filter-container" style={{ flexWrap: 'wrap', gap: '16px' }}>
                    <div className="search-input-wrapper" style={{ 
                        flex: '1 1 300px', 
                        maxWidth: '500px',
                        position: 'relative' 
                    }}>
                        <Search size={18} style={{ 
                            position: 'absolute', 
                            left: '16px', 
                            top: '50%', 
                            transform: 'translateY(-50%)',
                            color: 'var(--text-muted)'
                        }} />
                        <input
                            type="text"
                            placeholder="Buscar séries..."
                            value={searchQuery}
                            onChange={(e) => handleSearch(e.target.value)}
                            className="search-input"
                            style={{
                                width: '100%',
                                padding: '12px 16px 12px 48px',
                                borderRadius: '50px',
                                border: '1px solid var(--glass-border)',
                                background: 'var(--bg-card)',
                                color: 'var(--text-primary)',
                                fontSize: '1rem',
                                outline: 'none',
                                transition: 'all 0.2s'
                            }}
                        />
                    </div>
                </div>
                
                {error ? (
                    <div className="row-empty" style={{ color: '#ff4444', textAlign: 'center', padding: '40px' }}>
                        <p>{error}</p>
                        <button 
                            className="filter-chip" 
                            onClick={fetchSeries}
                            style={{ marginTop: '16px' }}
                        >
                            Tentar novamente
                        </button>
                    </div>
                ) : loading ? (
                    <div className="row-loading">
                        <div className="loading-spinner" />
                        <span>Carregando séries...</span>
                    </div>
                ) : (
                    <div className="catalog-grid">
                        {filteredSeries.map((s, index) => (
                           <div key={s.id || index} className="grid-item">
                               <MovieCard 
                                    movie={s} 
                                    index={index} 
                                    onClick={handleSeriesClick}
                                    isAvailable={true}
                               />
                           </div>
                        ))}
                    </div>
                )}
                
                {!loading && filteredSeries.length === 0 && !error && (
                     <div className="row-empty">
                        {searchQuery ? (
                            <>
                                <p>Nenhuma série encontrada para "{searchQuery}"</p>
                                <button 
                                    className="filter-chip" 
                                    onClick={() => { setSearchQuery(''); handleSearch(''); }}
                                    style={{ marginTop: '16px' }}
                                >
                                    Limpar busca
                                </button>
                            </>
                        ) : (
                            <>
                                <p>Nenhuma série encontrada no catálogo.</p>
                                <p style={{ fontSize: '0.85rem', opacity: 0.6, marginTop: '8px' }}>
                                    Total em cache: {series.length} | Stats: {stats.total}
                                </p>
                            </>
                        )}
                     </div>
                )}
            </div>

            {isSearchOpen && (
                <SearchModal 
                    onClose={() => setIsSearchOpen(false)} 
                    onMovieClick={handleSeriesClick} 
                />
            )}

            <AnimatePresence>
                {selectedSeries && (
                    <MovieDetailsModal 
                        movie={selectedSeries} 
                        onClose={closeModal} 
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default SeriesPage;
