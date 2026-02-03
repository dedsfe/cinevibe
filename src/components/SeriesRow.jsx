import { API_BASE_URL } from '../config';
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Tv } from 'lucide-react';

const SeriesCard = ({ series, index, onClick }) => {
  return (
    <motion.div
      className="movie-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.05, zIndex: 10 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => onClick(series)}
    >
      <div className="movie-poster-container">
        <img 
          src={series.poster_path || '/placeholder-poster.jpg'} 
          alt={series.title}
          className="movie-poster"
          loading="lazy"
        />
        <div className="movie-overlay">
          <div className="movie-actions">
            <motion.button 
              className="movie-action-btn primary"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Tv size={20} />
            </motion.button>
          </div>
          <div className="movie-info">
            <h3 className="movie-title">{series.title}</h3>
            <div className="movie-meta">
              {series.year && <span className="movie-year">{series.year}</span>}
              {series.rating > 0 && (
                <span className="movie-rating">★ {series.rating.toFixed(1)}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const SeriesRow = ({ title = "SÉRIES", onSeriesClick }) => {
  const [series, setSeries] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [scrollPosition, setScrollPosition] = useState(0);
  const rowRef = useRef(null);
  const sectionRef = useRef(null);

  // Intersection Observer - carrega só quando entra na tela
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasLoaded && !isLoading) {
            loadSeries();
          }
        });
      },
      {
        rootMargin: '100px',
        threshold: 0.1
      }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, [hasLoaded, isLoading]);

  const loadSeries = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/series?limit=50`);
      if (response.ok) {
        const data = await response.json();
        if (data?.results) {
          // Adiciona flag para identificar como série
          const seriesWithFlag = data.results.map(s => ({
            ...s,
            media_type: 'tv',
            isLocalSeries: true
          }));
          setSeries(seriesWithFlag);
        }
      }
      setHasLoaded(true);
    } catch (error) {
      console.error('Error loading series:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const scroll = (direction) => {
    if (rowRef.current) {
      const scrollAmount = direction === 'left' ? -800 : 800;
      rowRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
      setScrollPosition(rowRef.current.scrollLeft + scrollAmount);
    }
  };

  // Não mostra se não tiver séries
  if (hasLoaded && series.length === 0) return null;

  return (
    <section ref={sectionRef} className="movie-row">
      <h2 className="row-title">{title}</h2>
      
      {isLoading ? (
        <div className="row-loading">
          <div className="loading-spinner" />
          <span>Carregando séries...</span>
        </div>
      ) : series.length > 0 ? (
        <div className="row-container">
          <button 
            className="scroll-button left"
            onClick={() => scroll('left')}
            style={{ opacity: scrollPosition > 0 ? 1 : 0 }}
          >
            <ChevronLeft size={32} />
          </button>
          
          <div className="movies-slider" ref={rowRef}>
            {series.map((s, index) => (
              <SeriesCard 
                key={`${s.id}-${index}`} 
                series={s} 
                index={index} 
                onClick={onSeriesClick}
              />
            ))}
          </div>
          
          <button 
            className="scroll-button right"
            onClick={() => scroll('right')}
          >
            <ChevronRight size={32} />
          </button>
        </div>
      ) : hasLoaded ? (
        <div className="row-empty">Nenhuma série encontrada</div>
      ) : (
        <div className="row-placeholder" />
      )}
    </section>
  );
};

export default SeriesRow;
