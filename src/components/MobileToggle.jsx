import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Film, Tv, Home, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import '../styles/MobileToggle.css';

const MobileToggle = () => {
    const navigate = useNavigate();
    const location = useLocation();
    
    const isHome = location.pathname.includes('/home');
    const isMovies = location.pathname.includes('/movies');
    const isSeries = location.pathname.includes('/series');
    
    return (
        <div className="mobile-toggle-container">
            <div className="toggle-wrapper">
                <button 
                    className={`toggle-btn ${isHome ? 'active' : ''}`}
                    onClick={() => navigate('/home')}
                    style={{ position: 'relative' }}
                >
                    <span style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Home size={16} />
                        <span>Início</span>
                    </span>
                    {isHome && (
                        <motion.div 
                            className="active-pill"
                            layoutId="activePill"
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            style={{
                                position: 'absolute',
                                inset: 4,
                                background: 'rgba(255, 255, 255, 0.15)',
                                borderRadius: '100px',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                zIndex: 1
                            }}
                        />
                    )}
                </button>
                <button 
                    className={`toggle-btn ${isMovies ? 'active' : ''}`}
                    onClick={() => navigate('/movies')}
                    style={{ position: 'relative' }}
                >
                    <span style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Film size={16} />
                        <span>Filmes</span>
                    </span>
                    {isMovies && (
                        <motion.div 
                            className="active-pill"
                            layoutId="activePill"
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            style={{
                                position: 'absolute',
                                inset: 4,
                                background: 'rgba(255, 255, 255, 0.15)',
                                borderRadius: '100px',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                zIndex: 1
                            }}
                        />
                    )}
                </button>
                <button 
                    className={`toggle-btn ${isSeries ? 'active' : ''}`}
                    onClick={() => navigate('/series')}
                    style={{ position: 'relative' }}
                >
                    <span style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Tv size={16} />
                        <span>Séries</span>
                    </span>
                    {isSeries && (
                        <motion.div 
                            className="active-pill"
                            layoutId="activePill"
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            style={{
                                position: 'absolute',
                                inset: 4,
                                background: 'rgba(255, 255, 255, 0.15)',
                                borderRadius: '100px',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                zIndex: 1
                            }}
                        />
                    )}
                </button>
                <button 
                    className={`toggle-btn ${location.pathname.includes('/mylist') ? 'active' : ''}`}
                    onClick={() => navigate('/mylist')}
                    style={{ position: 'relative' }}
                >
                    <span style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Heart size={16} />
                        <span>Lista</span>
                    </span>
                    {location.pathname.includes('/mylist') && (
                        <motion.div 
                            className="active-pill"
                            layoutId="activePill"
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            style={{
                                position: 'absolute',
                                inset: 4,
                                background: 'rgba(255, 255, 255, 0.15)',
                                borderRadius: '100px',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                zIndex: 1
                            }}
                        />
                    )}
                </button>
            </div>
        </div>
    );
};

export default MobileToggle;
