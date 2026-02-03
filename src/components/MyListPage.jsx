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

const MyListPage = () => {
    const [myListMovies, setMyListMovies] = useState([]);
    const [myListSeries, setMyListSeries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadMyList();
    }, []);

    const loadMyList = async () => {
        setLoading(true);
        try {
            // Load movies from localStorage
            const movieIds = JSON.parse(localStorage.getItem('mylist_movies') || '[]');
            if (movieIds.length > 0) {
                // Fetch movie details from API
                const movies = [];
                for (const id of movieIds) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/cache/check-batch`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ tmdbIds: [id] })
                        });
                        if (response.ok) {
                            const data = await response.json();
                            if (data.statuses && data.statuses[String(id)]) {
                                movies.push({ id, embedUrl: data.statuses[String(id)] });
                            }
                        }
                    } catch (e) {
                        console.error('Error fetching movie:', e);
                    }
                }
                setMyListMovies(movies);
            }

            // Load series from localStorage
            const seriesIds = JSON.parse(localStorage.getItem('mylist_series') || '[]');
            if (seriesIds.length > 0) {
                const series = [];
                for (const id of seriesIds) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/series/${id}`);
                        if (response.ok) {
                            const data = await response.json();
                            series.push(data);
                        }
                    } catch (e) {
                        console.error('Error fetching series:', e);
                    }
                }
                setMyListSeries(series);
            }
        } catch (error) {
            console.error('Error loading my list:', error);
        } finally {
            setLoading(false);
        }
    };

    const removeFromList = (item, type) => {
        try {
            if (type === 'movie') {
                const myList = JSON.parse(localStorage.getItem('mylist_movies') || '[]');
                const newList = myList.filter(id => id !== item.id);
                localStorage.setItem('mylist_movies', JSON.stringify(newList));
                setMyListMovies(prev => prev.filter(m => m.id !== item.id));
            } else {
                const myList = JSON.parse(localStorage.getItem('mylist_series') || '[]');
                const newList = myList.filter(id => id !== item.id);
                localStorage.setItem('mylist_series', JSON.stringify(newList));
                setMyListSeries(prev => prev.filter(s => s.id !== item.id));
            }
        } catch (error) {
            console.error('Error removing from list:', error);
        }
    };

    const handleItemClick = (item) => {
        setSelectedItem(item);
    };

    const closeModal = () => {
        setSelectedItem(null);
    };

    const allItems = [...myListMovies, ...myListSeries];

    return (
        <div className="homepage">
            <Navbar onSearchClick={() => setIsSearchOpen(true)} />
            
            <div className="content-container catalog-container">
                <div className="catalog-header">
                    <h1 className="row-title">
                        <Heart size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
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
                        <span className="stats-badge">
                            TOTAL: {allItems.length}
                        </span>
                    </div>
                </div>

                {loading ? (
                    <div className="row-loading">
                        <div className="loading-spinner" />
                        <span>Carregando sua lista...</span>
                    </div>
                ) : allItems.length === 0 ? (
                    <div className="row-empty" style={{ padding: '60px 20px' }}>
                        <Heart size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                        <p style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Sua lista está vazia</p>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
                            Adicione filmes e séries para vê-los aqui
                        </p>
                        <button 
                            className="btn-primary"
                            onClick={() => navigate('/movies')}
                            style={{ padding: '12px 24px' }}
                        >
                            Explorar Filmes
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Movies Section */}
                        {myListMovies.length > 0 && (
                            <div style={{ marginBottom: '40px' }}>
                                <h2 style={{ 
                                    fontSize: '1.25rem', 
                                    marginBottom: '20px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}>
                                    <Film size={20} />
                                    Filmes ({myListMovies.length})
                                </h2>
                                <div className="catalog-grid">
                                    {myListMovies.map((movie, index) => (
                                        <div key={`movie-${movie.id}`} className="grid-item" style={{ position: 'relative' }}>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    removeFromList(movie, 'movie');
                                                }}
                                                style={{
                                                    position: 'absolute',
                                                    top: '8px',
                                                    right: '8px',
                                                    zIndex: 10,
                                                    background: 'rgba(229, 9, 20, 0.9)',
                                                    border: 'none',
                                                    borderRadius: '50%',
                                                    width: '32px',
                                                    height: '32px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    cursor: 'pointer',
                                                    color: 'white'
                                                }}
                                                title="Remover da lista"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                            <MovieCard 
                                                movie={movie} 
                                                index={index} 
                                                onClick={handleItemClick}
                                                isAvailable={true}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Series Section */}
                        {myListSeries.length > 0 && (
                            <div>
                                <h2 style={{ 
                                    fontSize: '1.25rem', 
                                    marginBottom: '20px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}>
                                    <Tv size={20} />
                                    Séries ({myListSeries.length})
                                </h2>
                                <div className="catalog-grid">
                                    {myListSeries.map((series, index) => (
                                        <div key={`series-${series.id}`} className="grid-item" style={{ position: 'relative' }}>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    removeFromList(series, 'series');
                                                }}
                                                style={{
                                                    position: 'absolute',
                                                    top: '8px',
                                                    right: '8px',
                                                    zIndex: 10,
                                                    background: 'rgba(229, 9, 20, 0.9)',
                                                    border: 'none',
                                                    borderRadius: '50%',
                                                    width: '32px',
                                                    height: '32px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    cursor: 'pointer',
                                                    color: 'white'
                                                }}
                                                title="Remover da lista"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                            <MovieCard 
                                                movie={series} 
                                                index={index} 
                                                onClick={handleItemClick}
                                                isAvailable={true}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {isSearchOpen && (
                <SearchModal 
                    onClose={() => setIsSearchOpen(false)} 
                    onMovieClick={handleItemClick} 
                />
            )}

            <AnimatePresence>
                {selectedItem && (
                    <MovieDetailsModal 
                        movie={selectedItem} 
                        onClose={closeModal} 
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default MyListPage;
