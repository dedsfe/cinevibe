import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
import '../styles/HomePage.css';

const streamingBrands = [
  { id: 'all', name: 'Para Você', logo: null, active: true },
  { id: 'netflix', name: 'Netflix', logo: 'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg' },
  { id: 'disney', name: 'Disney+', logo: 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg' },
  { id: 'hbo', name: 'HBO Max', logo: 'https://upload.wikimedia.org/wikipedia/commons/1/17/HBO_Max_Logo.svg' },
  { id: 'prime', name: 'Prime Video', logo: 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Prime_Video.png' },
  { id: 'apple', name: 'Apple TV+', logo: 'https://upload.wikimedia.org/wikipedia/commons/2/28/Apple_TV_Plus_Logo.svg' },
  { id: 'paramount', name: 'Paramount+', logo: 'https://upload.wikimedia.org/wikipedia/commons/4/4e/Paramount%2B_logo.svg' },
];

// Global movie cache
const movieCache = new Map();

const MovieModal = ({ movie, onClose }) => {
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
                    setSelectedWatchMovie(movie);
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
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const searchEmbed = async () => {
    setSearching(true);
    setError(null);
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/get-embed', {
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
                    <motion.button 
                      className="watch-open-btn"
                      onClick={openInNewTab}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <ExternalLink size={20} />
                      Abrir Player
                    </motion.button>
                  </div>
                </div>
                <div className="watch-info">
                  <p>Link encontrado! O player será aberto em uma nova aba.</p>
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

const MovieCard = ({ movie, index, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const genres = movie.genre_ids?.slice(0, 2).map(id => genreMap[id]).filter(Boolean) || [];
  
  return (
    <motion.div
      className="movie-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.08, zIndex: 10 }}
      onClick={() => onClick(movie)}
    >
      <div className="movie-card-inner">
        <img 
          src={getPosterUrl(movie.poster_path)} 
          alt={movie.title || movie.name}
          className="movie-poster"
          loading="lazy"
        />
        
        <AnimatePresence>
          {isHovered && (
            <motion.div 
              className="movie-card-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="movie-card-info">
                <h4 className="movie-title">{movie.title || movie.name}</h4>
                <div className="movie-meta">
                  <span className="movie-rating">
                    <Star size={14} fill="#ffd700" color="#ffd700" /> {movie.vote_average?.toFixed(1)}
                  </span>
                  <span className="movie-year">
                    {(movie.release_date || movie.first_air_date)?.substring(0, 4)}
                  </span>
                </div>
                <div className="movie-genres">
                  {genres.map((genre, i) => (
                    <span key={i} className="genre-tag">{genre}</span>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

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
      if (data?.results) {
        const validMovies = data.results
          .filter(movie => movie.poster_path)
          .slice(0, 15);
        setMovies(validMovies);
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

const Hero = ({ featured, onMovieClick }) => {
  if (!featured) return null;

  const genres = featured.genre_ids?.slice(0, 3).map(id => genreMap[id]).filter(Boolean) || [];

  return (
    <motion.div 
      className="hero"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <div className="hero-background">
        <img 
          src={getBackdropUrl(featured.backdrop_path)} 
          alt={featured.title || featured.name}
        />
        <div className="hero-gradient" />
      </div>
      
      <motion.div 
        className="hero-content"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.8 }}
      >
        <motion.span 
          className="hero-badge"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          #1 Em Alta Hoje
        </motion.span>
        
        <h1 className="hero-title">{featured.title || featured.name}</h1>
        
        <div className="hero-meta">
          <span className="hero-rating">
            <Star size={18} fill="#ffd700" color="#ffd700" /> {featured.vote_average?.toFixed(1)}
          </span>
          <span className="hero-year">{(featured.release_date || featured.first_air_date)?.substring(0, 4)}</span>
          <span className="hero-type">{featured.media_type === 'tv' ? 'Série' : 'Filme'}</span>
        </div>
        
        <div className="hero-genres">
          {genres.map((genre, i) => (
            <span key={i} className="hero-genre">{genre}</span>
          ))}
        </div>
        
        <p className="hero-overview">{featured.overview}</p>
        
        <div className="hero-buttons">
          <motion.button 
            className="btn-primary"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Play size={24} fill="currentColor" />
            Assistir Agora
          </motion.button>
          
          <motion.button 
            className="btn-secondary"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onMovieClick(featured)}
          >
            <Info size={24} />
            Mais Informações
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
};

const BrandNavbar = ({ selectedBrand, onBrandSelect }) => {
  return (
    <motion.div 
      className="brand-navbar"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.5 }}
    >
      <div className="brand-container">
        {streamingBrands.map((brand) => (
          <motion.button
            key={brand.id}
            className={`brand-button ${selectedBrand === brand.id ? 'active' : ''}`}
            onClick={() => onBrandSelect(brand.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {brand.logo ? (
              <img 
                src={brand.logo} 
                alt={brand.name}
                className="brand-logo"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
            ) : null}
            <span className="brand-name" style={{ display: brand.logo ? 'none' : 'flex' }}>
              {brand.name}
            </span>
            <span className="brand-name-fallback" style={{ display: 'none' }}>
              {brand.name}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
};

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav 
      className={`navbar ${scrolled ? 'scrolled' : ''}`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="nav-left">
        <div className="logo">CineVibe</div>
        <ul className="nav-links">
          <li><a href="#" className="active"><Home size={18} /> Início</a></li>
          <li><a href="#"><Film size={18} /> Filmes</a></li>
          <li><a href="#"><Tv size={18} /> Séries</a></li>
          <li><a href="#"><Heart size={18} /> Minha Lista</a></li>
        </ul>
      </div>
      
      <div className="nav-right">
        <button className="nav-icon">
          <Search size={22} />
        </button>
        <button className="nav-icon">
          <Bell size={22} />
        </button>
        <div className="profile">
          <User size={24} />
        </div>
      </div>
    </motion.nav>
  );
};

const HomePage = () => {
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [selectedWatchMovie, setSelectedWatchMovie] = useState(null);
  const [allMovies, setAllMovies] = useState([]);
  const [allTVShows, setAllTVShows] = useState([]);
  const [featured, setFeatured] = useState(null);
  const { fetchData } = useTMDB();
  const { myList, loading: myListLoading, refresh: refreshMyList } = useMyList();

  // Load movies and TV shows separately
  useEffect(() => {
    const loadContent = async () => {
      try {
        // Fetch movies and TV shows separately with delay
        const moviesData = await fetchData('/movie/popular');
        await new Promise(resolve => setTimeout(resolve, 300));
        
        const tvData = await fetchData('/tv/popular');
        
        // Process movies
        const movies = (moviesData?.results || [])
          .filter(item => item.poster_path)
          .map(item => ({ ...item, media_type: 'movie' }))
          .slice(0, 20);
        
        // Process TV shows
        const tvShows = (tvData?.results || [])
          .filter(item => item.poster_path)
          .map(item => ({ ...item, media_type: 'tv' }))
          .slice(0, 20);
        
        setAllMovies(movies);
        setAllTVShows(tvShows);
        
        // Set featured from movies
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
    ).slice(0, 12);
  };

  // Get trending movies
  const getTrendingMovies = () => {
    return allMovies.slice(0, 20);
  };

  // Get popular movies
  const getPopularMovies = () => {
    return allMovies
      .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
      .slice(0, 20);
  };

  // Get top rated movies
  const getTopRatedMovies = () => {
    return allMovies
      .sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0))
      .slice(0, 20);
  };

  return (
    <div className="homepage">
      <Navbar />
      <BrandNavbar selectedBrand={selectedBrand} onBrandSelect={setSelectedBrand} />
      <Hero featured={featured} onMovieClick={setSelectedMovie} />
      
      <div className="content-rows">
        {selectedBrand === 'all' ? (
          <>
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
                        onClick={setSelectedMovie}
                      />
                    ))}
                  </div>
                </div>
              </section>
            )}
            <LazyMovieRow title="Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Em Alta" fetchEndpoint="/trending/all/week" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Mais Bem Avaliados" fetchEndpoint="/movie/top_rated" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'netflix' ? (
          <>
            <LazyMovieRow title="Netflix - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Netflix - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'disney' ? (
          <>
            <LazyMovieRow title="Disney+ - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Disney+ - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'hbo' ? (
          <>
            <LazyMovieRow title="HBO Max - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="HBO Max - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'prime' ? (
          <>
            <LazyMovieRow title="Prime Video - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Prime Video - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'apple' ? (
          <>
            <LazyMovieRow title="Apple TV+ - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Apple TV+ - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : selectedBrand === 'paramount' ? (
          <>
            <LazyMovieRow title="Paramount+ - Filmes Populares" fetchEndpoint="/movie/popular" onMovieClick={setSelectedMovie} />
            <LazyMovieRow title="Paramount+ - Séries Populares" fetchEndpoint="/tv/popular" onMovieClick={setSelectedMovie} />
          </>
        ) : null}
      </div>
      
      <footer className="footer">
        <div className="footer-content">
          <p>© 2024 CineVibe. Todos os direitos reservados.</p>
          <p>Powered by TMDB</p>
        </div>
      </footer>

{selectedMovie && (
        <MovieModal 
          movie={selectedMovie} 
          onClose={() => {
            setSelectedMovie(null);
            refreshMyList();
          }} 
        />
      )}

      {selectedWatchMovie && (
        <WatchModal
          movie={selectedWatchMovie}
          onClose={() => setSelectedWatchMovie(null)}
        />
      )}
    </div>
  );
};

export default HomePage;