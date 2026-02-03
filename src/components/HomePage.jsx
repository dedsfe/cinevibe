import React, { useEffect, useState, useRef } from 'react';
import { API_BASE_URL } from '../config';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Bell, 
  User, 
  Play, 
  Info, 
  ChevronLeft, 
  ChevronRight,
  Star,
  Home,
  Film,
  Tv,
  Heart,
  X,
  Plus,
  ThumbsUp,
  Volume2,
  VolumeX,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { useTMDB, fetchCategories, getBackdropUrl, getPosterUrl, genreMap } from '../hooks/useTMDB';
import { useMyList } from '../hooks/useDatabase';
import { addToMyList, removeFromMyList, isInMyList } from '../db';
import MovieCard from './MovieCard';
import MovieDetailsModal from './MovieDetailsModal';
import Navbar from './Navbar';
import SearchModal from './SearchModal';
import MobileToggle from './MobileToggle';

const streamingBrands = [
  { id: 'disney', name: 'Disney', logo: 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg', video: 'https://static-assets.bamgrid.com/product/disneyplus/images/disney.1.2.66.a0100416954a621.mp4' },
  { id: 'pixar', name: 'Pixar', logo: 'https://upload.wikimedia.org/wikipedia/commons/d/df/Pixar_Animation_Studios_logo.svg', video: 'https://static-assets.bamgrid.com/product/disneyplus/images/pixar.1.2.66.a0100416954a621.mp4' },
  { id: 'marvel', name: 'Marvel', logo: 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Marvel_Logo.svg', video: 'https://static-assets.bamgrid.com/product/disneyplus/images/marvel.1.2.66.a0100416954a621.mp4' },
  { id: 'starwars', name: 'Star Wars', logo: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Star_Wars_Logo.svg', video: 'https://static-assets.bamgrid.com/product/disneyplus/images/star-wars.1.2.66.a0100416954a621.mp4' },
  { id: 'natgeo', name: 'National Geographic', logo: 'https://upload.wikimedia.org/wikipedia/commons/f/ff/National_Geographic_logo.svg', video: 'https://static-assets.bamgrid.com/product/disneyplus/images/national-geographic.1.2.66.a0100416954a621.mp4' },
];

// Global movie cache
const movieCache = new Map();

const MovieModal = ({ movie, onClose, onPlay }) => {
  const [trailer, setTrailer] = useState(null);
  const [isMuted, setIsMuted] = useState(true);
  const [dominantColor, setDominantColor] = useState('#1a1a1a');
  const [videoError, setVideoError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [watchProviders, setWatchProviders] = useState(null);
  const [isInList, setIsInList] = useState(false);
  const { fetchData } = useTMDB();

  // Check if movie is in list
  useEffect(() => {
    const checkList = async () => {
      const inList = await isInMyList(movie.id);
      setIsInList(inList);
    };
    checkList();
  }, [movie.id]);

  useEffect(() => {
    let isMounted = true;
    
    const loadMovieData = async () => {
      // Load trailer
      const videosEndpoint = movie.media_type === 'tv' 
        ? `/tv/${movie.id}/videos` 
        : `/movie/${movie.id}/videos`;
      
      // Load watch providers
      const providersEndpoint = movie.media_type === 'tv'
        ? `/tv/${movie.id}/watch/providers`
        : `/movie/${movie.id}/watch/providers`;
      
      try {
        const [videosData, providersData] = await Promise.all([
          fetchData(videosEndpoint),
          fetchData(providersEndpoint)
        ]);
        
        if (isMounted) {
          // Process trailer
          if (videosData?.results?.length > 0) {
            const officialTrailer = videosData.results.find(v => 
              v.type === 'Trailer' && v.site === 'YouTube'
            ) || videosData.results[0];
            setTrailer(officialTrailer);
          }
          
          // Process watch providers
          if (providersData?.results?.BR) {
            setWatchProviders(providersData.results.BR);
          } else if (providersData?.results?.US) {
            setWatchProviders(providersData.results.US);
          }
        }
      } catch (error) {
        console.log('Error loading movie data:', error);
        setVideoError(true);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    
    loadMovieData();
    
    return () => {
      isMounted = false;
    };
  }, [movie, fetchData]);

  useEffect(() => {
    const extractColor = async () => {
      try {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = getBackdropUrl(movie.backdrop_path);
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          canvas.width = 1;
          canvas.height = 1;
          ctx.drawImage(img, 0, 0, 1, 1);
          const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
          setDominantColor(`rgb(${r}, ${g}, ${b})`);
        };
      } catch (e) {
        console.log('Could not extract color');
      }
    };
    extractColor();
  }, [movie]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const genres = movie.genre_ids?.slice(0, 4).map(id => genreMap[id]).filter(Boolean) || [];
  const runtime = movie.runtime || movie.episode_run_time?.[0] || 120;

  const videoUrl = trailer?.key 
    ? `https://www.youtube-nocookie.com/embed/${trailer.key}?autoplay=1&mute=${isMuted ? 1 : 0}&controls=0&loop=1&playlist=${trailer.key}&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&vq=hd720&playsinline=1&enablejsapi=1&color=white`
    : null;

  return (
    <AnimatePresence>
      <motion.div 
        className="movie-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div 
          className="movie-modal"
          initial={{ opacity: 0, scale: 0.95, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 30 }}
          transition={{ type: 'spring', damping: 30, stiffness: 400 }}
          onClick={(e) => e.stopPropagation()}
        >
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>

          <div className="modal-hero" style={{
            background: `linear-gradient(180deg, ${dominantColor} 0%, rgba(15,15,15,0.95) 100%)`
          }}>
            <div className="modal-video-container">
              <img 
                src={getBackdropUrl(movie.backdrop_path)} 
                alt={movie.title || movie.name}
                className="modal-backdrop"
              />
              
              {!isLoading && videoUrl && !videoError && (
                <div className="video-wrapper">
                  <iframe
                    src={videoUrl}
                    title="Trailer"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    className="modal-video"
                  />
                </div>
              )}
              
              <div className="modal-video-overlay" />
              
              {videoUrl && (
                <button 
                  className="modal-mute-button"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                </button>
              )}
            </div>

            <div className="modal-content">
              <motion.h1 
                className="modal-title"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                {movie.title || movie.name}
              </motion.h1>

              <motion.div 
                className="modal-meta"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <span className="modal-rating">
                  <Star size={16} fill="#ffd700" color="#ffd700" />
                  {movie.vote_average?.toFixed(1)}
                </span>
                <span className="modal-year">
                  {(movie.release_date || movie.first_air_date)?.substring(0, 4)}
                </span>
                <span className="modal-type">
                  {movie.media_type === 'tv' ? 'Série' : 'Filme'}
                </span>
                <span className="modal-runtime">{runtime} min</span>
              </motion.div>

              <motion.div 
                className="modal-actions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <motion.button 
                  className="modal-btn-play"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    if (onClose) onClose();
                    if (onPlay) onPlay(movie);
                  }}
                >
                  <Play size={24} fill="currentColor" />
                  Assistir
                </motion.button>
                
                <motion.button 
                  className={`modal-btn-list ${isInList ? 'in-list' : ''}`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={async () => {
                    if (isInList) {
                      await removeFromMyList(movie.id);
                      setIsInList(false);
                    } else {
                      await addToMyList(movie);
                      setIsInList(true);
                    }
                  }}
                >
                  {isInList ? <Heart size={24} fill="currentColor" /> : <Plus size={24} />}
                  {isInList ? 'Na Lista' : 'Minha Lista'}
                </motion.button>
                
                <motion.button 
                  className="modal-btn-like"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <ThumbsUp size={24} />
                </motion.button>
              </motion.div>

              <motion.p 
                className="modal-overview"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                {movie.overview}
              </motion.p>

              <motion.div 
                className="modal-genres"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                {genres.map((genre, i) => (
                  <span key={i} className="modal-genre">{genre}</span>
                ))}
              </motion.div>

              {watchProviders?.flatrate && watchProviders.flatrate.length > 0 && (
                <motion.div 
                  className="modal-watch-providers"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                >
                  <h3 className="providers-title">Onde Assistir</h3>
                  <div className="providers-list">
                    {watchProviders.flatrate.map((provider) => (
                      <a
                        key={provider.provider_id}
                        href={getProviderLink(provider.provider_name, movie.title || movie.name)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="provider-link"
                      >
                        <img 
                          src={`https://image.tmdb.org/t/p/original${provider.logo_path}`}
                          alt={provider.provider_name}
                          className="provider-logo"
                        />
                        <span className="provider-name">{provider.provider_name}</span>
                      </a>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// Helper function to generate streaming service links
const getProviderLink = (providerName, movieTitle) => {
  const encodedTitle = encodeURIComponent(movieTitle);
  
  const providerLinks = {
    'Netflix': `https://www.netflix.com/search?q=${encodedTitle}`,
    'Disney Plus': `https://www.disneyplus.com/search?q=${encodedTitle}`,
    'HBO Max': `https://www.max.com/search?q=${encodedTitle}`,
    'Amazon Prime Video': `https://www.primevideo.com/search?k=${encodedTitle}`,
    'Apple TV Plus': `https://tv.apple.com/search?term=${encodedTitle}`,
    'Paramount Plus': `https://www.paramountplus.com/search/?q=${encodedTitle}`,
    'Globoplay': `https://globoplay.globo.com/busca/?q=${encodedTitle}`,
    'YouTube': `https://www.youtube.com/results?search_query=${encodedTitle}+filme`,
    'Google Play Movies': `https://play.google.com/store/search?q=${encodedTitle}&c=movies`,
    'Microsoft Store': `https://www.microsoft.com/search?q=${encodedTitle}`,
  };
  
  return providerLinks[providerName] || `https://www.google.com/search?q=${encodedTitle}+onde+assistir`;
};

const WatchModal = ({ movie, onClose }) => {
  const [embedUrl, setEmbedUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searching, setSearching] = useState(false);
  const [foundLink, setFoundLink] = useState(null);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    // Auto-search when modal opens
    searchEmbed();
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const searchEmbed = async () => {
    setSearching(true);
    setError(null);
    
    try {
        const response = await fetch(`${API_BASE_URL}/get-embed`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: movie.title || movie.name,
            tmdbId: movie.id
          }),
        });

        const data = await response.json();

        if (response.ok && data.embedUrl) {
           setFoundLink(data.embedUrl);
           setEmbedUrl(data.embedUrl);
           setLoading(false);
        } else {
           throw new Error(data.error || 'Link não encontrado');
        }

    } catch (err) {
        console.error("Erro ao buscar embed:", err);
        setError('Não foi possível encontrar um link disponível no momento.');
        setLoading(false);
    } finally {
        setSearching(false);
    }
  };

  const openInNewTab = () => {
    if (foundLink) {
      window.open(foundLink, '_blank');
    }
  };

  return (
    <AnimatePresence>
      <motion.div 
        className="watch-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div 
          className="watch-modal"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          onClick={(e) => e.stopPropagation()}
        >
          <button className="watch-modal-close" onClick={onClose}>
            <X size={24} />
          </button>

          <div className="watch-modal-header">
            <h2>{movie.title || movie.name}</h2>
            <span className="watch-modal-year">
              {(movie.release_date || movie.first_air_date)?.substring(0, 4)}
            </span>
          </div>

          <div className="watch-modal-content">
            {loading ? (
              <div className="watch-loading">
                <Loader2 className="spin" size={48} />
                <p>Preparando Player...</p>
                <span>Buscando melhor opção para você</span>
              </div>
            ) : error ? (
              <div className="watch-error">
                <p>{error}</p>
                <motion.button 
                  className="watch-retry-btn"
                  onClick={searchEmbed}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Tentar Novamente
                </motion.button>
              </div>
            ) : embedUrl ? (
              <div className="watch-player-container">
                <div className="watch-player-placeholder">
                  <div className="player-placeholder-content">
                    <Play size={64} />
                    <h3>Player Carregado</h3>
                    <p>O player foi preparado. Clique abaixo para assistir.</p>
                    <a 
                      className="watch-open-btn"
                      href={foundLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        textDecoration: 'none',
                        transform: 'scale(1)',
                        transition: 'transform 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                      onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                    >
                      <ExternalLink size={20} />
                      Abrir Player
                    </a>

                    <div style={{ marginTop: '20px', width: '100%', maxWidth: '400px' }}>
                      <p style={{ fontSize: '0.9rem', marginBottom: '5px', opacity: 0.8 }}>Caso a janela não abra, copie o link:</p>
                      <input 
                        type="text" 
                        value={embedUrl} 
                        readOnly 
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderRadius: '4px',
                          border: '1px solid #333',
                          background: '#1a1a1a',
                          color: '#fff'
                        }}
                        onClick={(e) => e.target.select()}
                      />
                    </div>
                  </div>
                </div>
                <div className="watch-info">
                  <p>Link encontrado! O player deve abrir em uma nova aba.</p>
                </div>
              </div>
            ) : (
              <div className="watch-searching">
                <motion.button 
                  className="watch-search-btn"
                  onClick={searchEmbed}
                  disabled={searching}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {searching ? (
                    <>
                      <Loader2 className="spin" size={24} />
                      Buscando...
                    </>
                  ) : (
                    <>
                      <Search size={24} />
                      Buscar Link
                    </>
                  )}
                </motion.button>
                <p className="watch-search-info">
                  Clique para buscar links de streaming disponíveis
                </p>
              </div>
            )}
          </div>

          <div className="watch-modal-footer">
            <button className="watch-footer-link" onClick={openInNewTab} disabled={!foundLink}>
              Abrir em nova aba
            </button>
            <span className="watch-footer-note">
              Os links são buscados em tempo real
            </span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// SearchModal imported from ./SearchModal

// ... existing LazyMovieRow ...
const LazyMovieRow = ({ title, fetchEndpoint, onMovieClick }) => {
  const [movies, setMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [scrollPosition, setScrollPosition] = useState(0);
  const { fetchData } = useTMDB();
  const rowRef = useRef(null);
  const sectionRef = useRef(null);

  // Intersection Observer - carrega só quando entra na tela
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasLoaded && !isLoading) {
            loadMovies();
          }
        });
      },
      {
        rootMargin: '100px', // Começa a carregar 100px antes de entrar na tela
        threshold: 0.1
      }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, [hasLoaded, isLoading]);

  const loadMovies = async () => {
    setIsLoading(true);
    try {
      const data = await fetchData(fetchEndpoint);
      console.log(`[LazyMovieRow: ${title}] Data received:`, data?.results?.length || 0, 'movies');
      if (data?.results) {
        const validMovies = data.results
          .filter(movie => movie.poster_path)
          .slice(0, 100);
        console.log(`[LazyMovieRow: ${title}] After poster filter:`, validMovies.length, 'movies');
        
        // Batch check availability
        const tmdbIds = validMovies.map(m => m.id);
        if (tmdbIds.length > 0) {
            try {
                const checkRes = await fetch(`${API_BASE_URL}/cache/check-batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tmdbIds })
                });
                if (checkRes.ok) {
                    const checkData = await checkRes.json();
                    const statuses = checkData.statuses || {};
                    
                    // Mark availability
                    validMovies.forEach(m => {
                        const status = statuses[String(m.id)];
                        m.isAvailable = status && status !== "NOT_FOUND";
                    });

                    // Filter only available ones
                    const filteredMovies = validMovies.filter(m => m.isAvailable);
                    console.log(`[LazyMovieRow: ${title}] After availability filter:`, filteredMovies.length, 'movies');
                    setMovies(filteredMovies);
                } else {
                    // Fallback: if check fails, show all to avoid total empty (optional, but safer for TMDB rows)
                    setMovies(validMovies);
                }
            } catch (err) {
                console.warn("Failed to check batch availability", err);
                setMovies(validMovies);
            }
        } else {
            setMovies(validMovies);
        }
        setHasLoaded(true);
      }
    } catch (error) {
      console.error('Error loading movies:', error);
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

  // Hide rows with < 5 movies (unless it's the Family category)
  if (hasLoaded && movies.length < 5 && title !== "FAMÍLIA") return null;

  return (
    <section ref={sectionRef} className="movie-row">
      <h2 className="row-title">{title}</h2>
      
      {isLoading ? (
        <div className="row-loading">
          <div className="loading-spinner" />
          <span>Carregando...</span>
        </div>
      ) : movies.length > 0 ? (
        <div className="row-container">
          <button 
            className="scroll-button left"
            onClick={() => scroll('left')}
            style={{ opacity: scrollPosition > 0 ? 1 : 0 }}
          >
            <ChevronLeft size={32} />
          </button>
          
          <div className="movies-slider" ref={rowRef}>
            {movies.map((movie, index) => (
              <MovieCard 
                key={`${movie.id}-${index}`} 
                movie={movie} 
                index={index} 
                onClick={onMovieClick}
                isAvailable={movie.isAvailable}
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
        <div className="row-empty">Nenhum filme encontrado</div>
      ) : (
        <div className="row-placeholder" />
      )}
    </section>
  );
};

const HeroCarousel = ({ items, onMovieClick }) => {
  if (!items || items.length === 0) return null;

  const [currentIndex, setCurrentIndex] = useState(0);
  const current = items[currentIndex];

  useEffect(() => {
    if (items.length <= 1) return;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % items.length);
    }, 8000);
    return () => clearInterval(timer);
  }, [items.length]);

  const swipeConfidenceThreshold = 10000;
  const swipePower = (offset, velocity) => {
    return Math.abs(offset) * velocity;
  };

  const hasPaginated = useRef(false);

  const paginate = (newDirection) => {
    if (newDirection === 1) {
      setCurrentIndex((prev) => (prev + 1) % items.length);
    } else {
      setCurrentIndex((prev) => (prev - 1 + items.length) % items.length);
    }
  };

  return (
    <div className="hero-carousel">
      <AnimatePresence mode="wait">
        <motion.div 
          key={current.id}
          className="hero-slide"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1 }}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={1}
          onDragEnd={(e, { offset, velocity }) => {
            const swipe = swipePower(offset.x, velocity.x);

            if (swipe < -swipeConfidenceThreshold) {
              paginate(1);
            } else if (swipe > swipeConfidenceThreshold) {
              paginate(-1);
            }
          }}
        >
          <div 
            className="hero-background" 
            onClick={() => onMovieClick(current)}
            style={{ cursor: 'pointer' }}
          >
            <img 
              src={getBackdropUrl(current.backdrop_path)} 
              alt={current.title || current.name}
              draggable="false"
            />
            <div className="hero-gradient" />
          </div>
          
          <motion.div 
            className="hero-content"
            initial={{ opacity: 0, x: -100 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            <h1 className="hero-title">{current.title || current.name}</h1>
            <p className="hero-overview">{current.overview}</p>
            
            <div className="hero-buttons">
              <motion.button 
                className="btn-primary"
                whileTap={{ scale: 0.95 }}
                onClick={() => onMovieClick(current)}
              >
                <Play size={20} fill="currentColor" stroke="none" />
                <span>ASSISTIR AGORA</span>
              </motion.button>
              
              <motion.button 
                className="btn-secondary"
                whileTap={{ scale: 0.95 }}
                onClick={() => onMovieClick(current)}
              >
                DETALHES
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>
      
      <div className="carousel-indicators">
        {items.map((_, i) => (
          <div 
            key={i} 
            className={`indicator ${i === currentIndex ? 'active' : ''}`}
            onClick={() => setCurrentIndex(i)}
          />
        ))}
      </div>
    </div>
  );
};

// Streaming brands with recognizable logos
const pillBrands = [
  { 
    id: 'netflix', 
    name: 'Netflix', 
    color: '#E50914'
  },
  { 
    id: 'max', 
    name: 'Max', 
    color: '#002BE7'
  },
  { 
    id: 'disney', 
    name: 'Disney+', 
    color: '#113CCF'
  },
  { 
    id: 'prime', 
    name: 'Prime Video', 
    color: '#00A8E1'
  },
  { 
    id: 'paramount', 
    name: 'Paramount+', 
    color: '#0064FF'
  },
  { 
    id: 'apple', 
    name: 'Apple TV+', 
    color: '#FFFFFF'
  },
];

// SVG Icons for streaming services
const StreamingIcon = ({ name, color, size = 28 }) => {
  const icons = {
    netflix: (
      <svg viewBox="0 0 111 300" width={size} height={size * 2.7} fill={color}>
        <path d="M55.5 0L55.5 112.5L55.5 0M55.5 187.5L55.5 300L55.5 187.5" stroke={color} strokeWidth="40"/>
        <path d="M0 0L55.5 112.5L111 0M0 300L55.5 187.5L111 300" stroke={color} strokeWidth="40" fill="none"/>
      </svg>
    ),
    max: (
      <svg viewBox="0 0 300 150" width={size * 2} height={size} fill={color}>
        <path d="M0 0H50V100H0V0ZM60 50L85 0H100L125 50L150 0H165L140 50L165 100H140L115 50L90 100H65L90 50L65 0H40L60 50Z" fill="white"/>
        <circle cx="185" cy="50" r="50" fill={color}/>
      </svg>
    ),
    disney: (
      <svg viewBox="0 0 400 200" width={size * 2} height={size} fill={color}>
        <text x="20" y="120" fontFamily="serif" fontSize="80" fontWeight="bold" fill="white">Disney</text>
        <text x="280" y="120" fontFamily="sans-serif" fontSize="60" fill={color}>+</text>
        <path d="M220 130 A 30 30 0 1 1 220 170" fill="none" stroke={color} strokeWidth="3"/>
      </svg>
    ),
    prime: (
      <svg viewBox="0 0 400 150" width={size * 2.7} height={size} fill={color}>
        <text x="10" y="90" fontFamily="sans-serif" fontSize="60" fontWeight="bold" fill="#00A8E1">prime</text>
        <text x="200" y="90" fontFamily="sans-serif" fontSize="40" fill="white">video</text>
        <path d="M320 40 Q 350 60 350 90 Q 350 120 320 120" fill="none" stroke="#FF9900" strokeWidth="8" strokeLinecap="round"/>
      </svg>
    ),
    paramount: (
      <svg viewBox="0 0 300 150" width={size * 2} height={size} fill={color}>
        <polygon points="150,20 280,130 20,130" fill="#0064FF"/>
        <text x="75" y="115" fontFamily="sans-serif" fontSize="35" fontWeight="bold" fill="white">Paramount</text>
        <text x="240" y="115" fontFamily="sans-serif" fontSize="40" fill="white">+</text>
        <circle cx="150" cy="90" r="8" fill="white"/>
      </svg>
    ),
    apple: (
      <svg viewBox="0 0 300 100" width={size * 3} height={size} fill={color}>
        <path d="M85 30 C 85 20, 95 15, 105 20 C 100 10, 85 10, 75 20 C 70 25, 70 35, 75 40 C 65 45, 55 40, 50 30 C 45 40, 55 55, 70 55 C 65 65, 55 75, 40 70 C 50 85, 75 90, 90 75 C 100 90, 130 85, 140 70 C 125 75, 115 65, 110 55 C 125 55, 135 40, 130 30 C 125 40, 115 45, 105 40 C 110 35, 110 25, 105 20" fill="white"/>
        <text x="150" y="60" fontFamily="sans-serif" fontSize="35" fill="white">TV+</text>
      </svg>
    ),
  };
  
  return icons[name] || null;
};

const BrandPillNavbar = () => {
  return (
    <div className="brand-pill-container">
      <div className="brand-pill-navbar">
        <motion.button 
          className="brand-pill-item active"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="brand-pill-text">Para Você</span>
        </motion.button>
        {pillBrands.map((brand) => (
          <motion.div 
            key={brand.id} 
            className="brand-pill-item"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title={brand.name}
          >
            <StreamingIcon name={brand.id} color={brand.color} size={24} />
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Navbar imported from ./Navbar

const HomePage = () => {
  const navigate = useNavigate();
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [selectedWatchMovie, setSelectedWatchMovie] = useState(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [allMovies, setAllMovies] = useState([]);
  const [allTVShows, setAllTVShows] = useState([]);
  const [featured, setFeatured] = useState(null);
  const { fetchData } = useTMDB();
  const { myList, loading: myListLoading, refresh: refreshMyList } = useMyList();

  const handleMovieClick = (movie) => {
    setSelectedMovie(movie);
  };

  const closeModal = () => {
    setSelectedMovie(null);
  };

  const handleSearchClose = () => {
    setIsSearchOpen(false);
  };

  // Load movies and TV shows separately
  useEffect(() => {
    const loadContent = async () => {
      try {
        const moviesData = await fetchData('/movie/popular');
        await new Promise(resolve => setTimeout(resolve, 300));
        
        const tvData = await fetchData('/tv/popular');
        
        const movies = (moviesData?.results || [])
          .filter(item => item.poster_path)
          .map(item => ({ ...item, media_type: 'movie' }))
          .slice(0, 50);
        
        const tvShows = (tvData?.results || [])
          .filter(item => item.poster_path)
          .map(item => ({ ...item, media_type: 'tv' }))
          .slice(0, 50);
        
        setAllMovies(movies);
        setAllTVShows(tvShows);
        
        if (movies.length > 0) {
          setFeatured(movies[0]);
        }
      } catch (error) {
        console.error('Error loading content:', error);
      }
    };
    
    loadContent();
  }, [fetchData]);

  // Filter movies by genre
  const getMoviesByGenre = (genreId) => {
    return allMovies.filter(movie =>
      movie.genre_ids?.includes(genreId)
    ).slice(0, 50);
  };

  return (
    <div className="homepage">
      <Navbar onSearchClick={() => setIsSearchOpen(true)} />
      <div style={{ marginTop: '20px', marginBottom: '-20px', position: 'relative', zIndex: 90 }}>
        <MobileToggle />
      </div>
      <HeroCarousel 
        items={allMovies.slice(0, 5)} 
        onMovieClick={handleMovieClick}
      />
      
      <div className="content-container">
        {myList.length > 0 && (
          <section className="movie-row">
            <h2 className="row-title">Minha Lista</h2>
            <div className="row-container">
              <div className="movies-slider">
                {myList.map((movie, index) => (
                  <MovieCard 
                    key={`${movie.id}-${index}`} 
                    movie={movie} 
                    index={index} 
                    onClick={handleMovieClick}
                  />
                ))}
              </div>
            </div>
          </section>
        )}
        
        <LazyMovieRow 
          title="CATÁLOGO ORIGINAL" 
          fetchEndpoint="/api/catalog?limit=100"
          onMovieClick={handleMovieClick}
        />
        <LazyMovieRow title="EM ALTA (MUNDIAL)" fetchEndpoint="/trending/all/day" onMovieClick={handleMovieClick} />
        <LazyMovieRow title="AÇÃO & AVENTURA" fetchEndpoint={fetchCategories.action} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="COMÉDIA" fetchEndpoint={fetchCategories.comedy} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="TERROR & SUSPENSE" fetchEndpoint={fetchCategories.horror} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="FICÇÃO CIENTÍFICA" fetchEndpoint={fetchCategories.scifi} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="DRAMA" fetchEndpoint={fetchCategories.drama} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="FAMÍLIA" fetchEndpoint={fetchCategories.family} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="ANIMAÇÃO" fetchEndpoint={fetchCategories.animation} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="FANTASIA" fetchEndpoint={fetchCategories.fantasy} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="DOCUMENTÁRIOS" fetchEndpoint={fetchCategories.documentary} onMovieClick={handleMovieClick} />
        <LazyMovieRow title="MAIS VOTADOS" fetchEndpoint={fetchCategories.topRated} onMovieClick={handleMovieClick} />
      </div>

      {isSearchOpen && (
        <SearchModal onClose={handleSearchClose} onMovieClick={handleMovieClick} />
      )}
      
      <AnimatePresence>
        {selectedMovie && (
          <MovieDetailsModal 
            movie={selectedMovie} 
            onClose={closeModal} 
          />
        )}
      </AnimatePresence>
      
      <footer className="footer">
        <div className="footer-content">
          <p>© 2024 Filfil. Todos os direitos reservados.</p>
          <p>Powered by TMDB</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;