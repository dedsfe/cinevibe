import { API_BASE_URL } from '../config';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Film, Tv, Trash2 } from 'lucide-react';
import Navbar from './Navbar';
import SearchModal from './SearchModal';
import MovieCard from './MovieCard';
import MovieDetailsModal from './MovieDetailsModal';
import '../styles/HomePage.css';
import '../styles/MoviesPage.css';
import MobileToggle from './MobileToggle';

const MyListPage = () => {
    const [myListMovies, setMyListMovies] = useState([]);
    const [myListSeries, setMyListSeries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    const [seriesData, setSeriesData] = useState(null); // For modal
    const navigate = useNavigate();

    useEffect(() => {
        loadMyList();
    }, []);

    const loadMyList = async () => {
        setLoading(true);
        try {
            // Load movies
            const movieIds = JSON.parse(localStorage.getItem('mylist_movies') || '[]');
            const moviePromises = movieIds.map(id => 
                fetch(`${API_BASE_URL}/movie/${id}`)
                    .then(res => res.ok ? res.json() : null)
                    .catch(e => null)
            );
            const movies = (await Promise.all(moviePromises)).filter(m => m !== null);
            setMyListMovies(movies);

            // Load series
            const seriesIds = JSON.parse(localStorage.getItem('mylist_series') || '[]');
            const seriesPromises = seriesIds.map(id => 
               fetch(`${API_BASE_URL}/series/${id}`)
                    .then(res => res.ok ? res.json() : null)
                    .catch(e => null)
            );
            const series = (await Promise.all(seriesPromises)).filter(s => s !== null);
            setMyListSeries(series.map(s => ({ ...s, media_type: 'tv' })));

        } catch (error) {
            console.error('Error loading my list:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleItemClick = async (item) => {
        if (item.media_type === 'tv' || item.seasons) {
            setSeriesData(item); 
            setSelectedItem(item);
        } else {
            setSeriesData(null);
            setSelectedItem(item);
        }
    };

    const closeModal = () => {
        setSelectedItem(null);
        setSeriesData(null);
    };

    // Callback when user toggles list in modal, update local state
    const handleListChange = () => {
        loadMyList();
    };

    const allItems = [...myListMovies, ...myListSeries];

    return (
        <div className="homepage">
            <Navbar onSearchClick={() => setIsSearchOpen(true)} />
            
            <div style={{ marginTop: '110px', display: 'flex', justifyContent: 'center', position: 'relative', zIndex: 10 }}>
                <MobileToggle />
            </div>

            <div className="content-container catalog-container" style={{ paddingTop: '20px' }}>
                <div className="catalog-header">
                    <h1 className="row-title">
                        <Heart size={32} style={{ marginRight: '12px', verticalAlign: 'middle', color: 'var(--accent-color)' }} />
                        Minha Lista
                    </h1>
                    
                    <div className="catalog-stats">
                        <span className="stats-badge">
                            <Film size={14} />
                            {myListMovies.length} FILMES
                        </span>
                        <span className="stats-badge available">
                            <Tv size={14} />
                            {myListSeries.length} SÉRIES
                        </span>
                    </div>
                </div>



                {loading ? (
                    <div className="row-loading">
                        <div className="loading-spinner" />
                        <span>Carregando sua biblioteca...</span>
                    </div>
                ) : allItems.length === 0 ? (
                    <div className="row-empty" style={{ padding: '60px 20px', textAlign: 'center' }}>
                        <Heart size={64} style={{ opacity: 0.2, marginBottom: '24px' }} />
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '12px' }}>Sua lista está vazia</h2>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '32px', maxWidth: '400px', margin: '0 auto 32px' }}>
                            Salve filmes e séries aqui para assistir mais tarde.
                        </p>
                        <button 
                            className="netflix-btn"
                            onClick={() => navigate('/home')}
                        >
                            Explorar Catálogo
                        </button>
                    </div>
                ) : (
                    <div className="movies-grid">
                        {allItems.map((item, index) => (
                            <div key={`${item.id}-${index}`} className="grid-item">
                                <MovieCard 
                                    movie={item} 
                                    index={index} 
                                    onClick={handleItemClick}
                                    isAvailable={true}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <AnimatePresence>
                {selectedItem && (
                    <MovieDetailsModal 
                        movie={selectedItem} 
                        onClose={closeModal}
                        isSeries={selectedItem.media_type === 'tv' || !!selectedItem.seasons}
                        seriesData={seriesData} // Pass text/series data
                        onListChange={handleListChange} // Refresh list if removed
                    />
                )}
                {isSearchOpen && (
                    <SearchModal onClose={() => setIsSearchOpen(false)} />
                )}
            </AnimatePresence>
        </div>
    );
};

export default MyListPage;
