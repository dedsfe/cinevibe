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
import MobileToggle from './MobileToggle';

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
    const [visibleCount, setVisibleCount] = useState(24);
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
            
            // CACHE CHECK
            const CACHE_KEY = 'cinevibe_series_cache';
            const CACHE_DURATION = 1000 * 60 * 10; // 10 minutes
            
            const cached = sessionStorage.getItem(CACHE_KEY);
            if (cached) {
                const { data, timestamp } = JSON.parse(cached);
                if (Date.now() - timestamp < CACHE_DURATION) {
                    console.log("[SeriesPage] Using cached series data");
                    setSeries(data);
                    setFilteredSeries(data);
                    setStats({ total: data.length });
                    setLoading(false);
                    return;
                }
            }

            console.log("[SeriesPage] Fetching series from API...");
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
                
                // SAVE TO CACHE
                sessionStorage.setItem(CACHE_KEY, JSON.stringify({
                    data: allSeries,
                    timestamp: Date.now()
                }));
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
            
            <div style={{ marginTop: '110px', display: 'flex', justifyContent: 'center', position: 'relative', zIndex: 10 }}>
                <MobileToggle />
            </div>

            <div className="content-container catalog-container" style={{ paddingTop: '20px' }}>
                <div className="catalog-header">
                    <h1 className="row-title">
                        <Tv size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
                        SÉRIES
                    </h1>
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
                    <>
                        <div className="catalog-grid">
                            {filteredSeries.slice(0, visibleCount).map((s, index) => (
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
                        
                        {visibleCount < filteredSeries.length && (
                            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '40px' }}>
                                <button 
                                    className="netflix-btn-play"
                                    onClick={() => setVisibleCount(prev => prev + 24)}
                                    style={{ 
                                        minWidth: '200px', 
                                        background: 'rgba(255, 255, 255, 0.1) !important',
                                        backdropFilter: 'blur(10px)',
                                        color: 'white !important',
                                        border: '1px solid rgba(255, 255, 255, 0.1)'
                                    }}
                                >
                                    Carregar Mais
                                </button>
                            </div>
                        )}
                    </>
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
