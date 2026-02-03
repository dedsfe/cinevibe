import { API_BASE_URL } from '../config';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, Plus, Check, Star, Volume2, VolumeX, ChevronDown } from 'lucide-react';
import { useTMDB, getBackdropUrl, getPosterUrl, genreMap } from '../hooks/useTMDB';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import '../styles/MovieDetailsModal.css';

// Helper functions for image URLs
const getImageUrl = (path, fallback = '') => {
  if (!path) return fallback;
  if (path.startsWith('http')) return path;
  return `https://image.tmdb.org/t/p/w500${path}`;
};

const getBackdropImageUrl = (path, fallback = '') => {
  if (!path) return fallback;
  if (path.startsWith('http')) return path;
  return `https://image.tmdb.org/t/p/w1280${path}`;
};

const MovieDetailsModal = ({ movie, onClose }) => {
  const [trailer, setTrailer] = useState(null);
  const [cast, setCast] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [inList, setInList] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [selectedSimilarMovie, setSelectedSimilarMovie] = useState(null);
  const [isSeries, setIsSeries] = useState(false);
  const [seriesData, setSeriesData] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(null);
  const [selectedSeasonNumber, setSelectedSeasonNumber] = useState(null);
  const [loadingSeries, setLoadingSeries] = useState(false);
  const iframeRef = React.useRef(null);
  const { fetchData } = useTMDB();
  const { getAuthHeaders } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const loadDetails = async () => {
      // Verificar se é uma série da nossa base (tem opera_id)
      if (movie.opera_id) {
        setIsSeries(true);
        // Check if series is in my list via API
        try {
          const response = await fetch(`${API_BASE_URL}/mylist/series/${movie.id}/check`, {
            headers: getAuthHeaders()
          });
          if (response.ok) {
            const data = await response.json();
            setInList(data.in_list);
          }
        } catch (e) {
          console.error('Error checking series in list:', e);
        }
        await loadSeriesData(movie.id);
        return;
      }

      // Check if in list via API
      try {
        const response = await fetch(`${API_BASE_URL}/mylist/movies/${movie.id}/check`, {
          headers: getAuthHeaders()
        });
        if (response.ok) {
          const data = await response.json();
          setInList(data.in_list);
        }
      } catch (e) {
        console.error('Error checking movie in list:', e);
      }

      // Fetch videos (trailers)
      const endpoint = movie.media_type === 'tv' ? `/tv/${movie.id}/videos` : `/movie/${movie.id}/videos`;
      const videosData = await fetchData(endpoint);
      if (videosData?.results) {
        const officialTrailer = videosData.results.find(
          v => v.type === 'Trailer' && (v.site === 'YouTube' || v.site === 'Vimeo')
        ) || videosData.results[0];
        setTrailer(officialTrailer);
      }

      // Fetch credits (cast)
      const creditsEndpoint = movie.media_type === 'tv' ? `/tv/${movie.id}/credits` : `/movie/${movie.id}/credits`;
      const creditsData = await fetchData(creditsEndpoint);
      if (creditsData?.cast) {
        setCast(creditsData.cast.slice(0, 6));
      }

      // Fetch similar movies
      const similarEndpoint = movie.media_type === 'tv' ? `/tv/${movie.id}/similar` : `/movie/${movie.id}/similar`;
      const similarData = await fetchData(similarEndpoint);
      if (similarData?.results) {
        setSimilar(similarData.results.slice(0, 6));
      }
    };

    // Só carrega detalhes se for filme normal OU se for série mas ainda não temos os dados
    const shouldLoad = movie?.id && (!movie.opera_id || !seriesData);
    if (shouldLoad) {
      loadDetails();
    }
  }, [movie, fetchData, seriesData]);

  const loadSeriesData = async (seriesId) => {
    setLoadingSeries(true);
    try {
      const response = await fetch(`${API_BASE_URL}/series/${seriesId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('[loadSeriesData] Loaded series:', data.title, 'Seasons:', data.seasons?.length);
        setSeriesData(data);
        if (data.seasons && data.seasons.length > 0) {
          const firstSeason = data.seasons[0];
          console.log('[loadSeriesData] Setting initial season:', firstSeason.season_number, 'with', firstSeason.episodes?.length, 'episodes');
          setSelectedSeason(firstSeason);
          setSelectedSeasonNumber(firstSeason.season_number);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar série:', error);
    } finally {
      setLoadingSeries(false);
    }
  };

  // Handle Mute/Unmute
  useEffect(() => {
    if (iframeRef.current && trailer) {
      const command = isMuted ? 'mute' : 'unMute';
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({ event: 'command', func: command, args: [] }),
        '*'
      );
    }
  }, [isMuted, trailer]);

  const handleWatchNow = () => {
    if (isSeries && selectedSeason?.episodes?.length > 0) {
      // Para séries, assistir o primeiro episódio da temporada selecionada
      const firstEpisode = selectedSeason.episodes[0];
      navigate(`/watch/${movie.id}`, { 
        state: { 
          movie: {
            ...movie,
            videoUrl: firstEpisode.video_url,
            episodeTitle: firstEpisode.title,
            seasonNumber: selectedSeason.season_number,
            episodeNumber: firstEpisode.episode_number
          }
        } 
      });
    } else {
      navigate(`/watch/${movie.id}`, { state: { movie } });
    }
    onClose();
  };

  const handleWatchEpisode = (episode) => {
    navigate(`/watch/${movie.id}`, { 
      state: { 
        movie: {
          ...movie,
          videoUrl: episode.video_url,
          episodeTitle: episode.title,
          seasonNumber: selectedSeason.season_number,
          episodeNumber: episode.episode_number
        }
      } 
    });
    onClose();
  };

  const handleToggleList = async () => {
    if (isSeries) {
      // Handle series via API
      try {
        if (inList) {
          const response = await fetch(`${API_BASE_URL}/mylist/series/${movie.id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
          });
          if (response.ok) {
            setInList(false);
          }
        } else {
          const response = await fetch(`${API_BASE_URL}/mylist/series`, {
            method: 'POST',
            headers: {
              ...getAuthHeaders(),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ series_id: movie.id })
          });
          if (response.ok) {
            setInList(true);
          }
        }
      } catch (e) {
        console.error('Error toggling series in list:', e);
      }
    } else {
      // Handle movies via API
      try {
        if (inList) {
          const response = await fetch(`${API_BASE_URL}/mylist/movies/${movie.id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
          });
          if (response.ok) {
            setInList(false);
          }
        } else {
          const response = await fetch(`${API_BASE_URL}/mylist/movies`, {
            method: 'POST',
            headers: {
              ...getAuthHeaders(),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(movie)
          });
          if (response.ok) {
            setInList(true);
          }
        }
      } catch (e) {
        console.error('Error toggling movie in list:', e);
      }
    }
  };

  const handleSimilarClick = (similarMovie) => {
    setSelectedSimilarMovie(similarMovie);
  };

  const handleCloseSimilarModal = () => {
    setSelectedSimilarMovie(null);
  };

  const getYear = () => {
    if (isSeries) {
      return movie.year || '';
    }
    const dateStr = movie.release_date || movie.first_air_date;
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return isNaN(date.getFullYear()) ? dateStr.split('-')[0] : date.getFullYear();
  };

  const getGenres = () => {
    // Se genres for uma string (nossa API), retorna diretamente
    if (typeof movie.genres === 'string') {
      return movie.genres;
    }
    // Se for array de objetos (TMDB)
    if (Array.isArray(movie.genres) && movie.genres.length > 0) {
      return movie.genres.map(g => g.name).join(' • ');
    }
    // Se for array de IDs (TMDB)
    if (Array.isArray(movie.genre_ids) && movie.genre_ids.length > 0) {
      return movie.genre_ids.map(id => genreMap[id] || id).join(' • ');
    }
    return '';
  };

  const getRuntime = () => {
    if (isSeries) {
      const seasonCount = seriesData?.seasons?.length || 0;
      const episodeCount = seriesData?.seasons?.reduce((acc, s) => acc + (s.episodes?.length || 0), 0) || 0;
      if (seasonCount > 0) {
        return `${seasonCount} temp${seasonCount > 1 ? 's' : ''} • ${episodeCount} ep${episodeCount > 1 ? 's' : ''}`;
      }
      return null;
    }
    if (movie.runtime) {
      const hours = Math.floor(movie.runtime / 60);
      const mins = movie.runtime % 60;
      return `${hours}h ${mins}m`;
    }
    if (movie.episode_run_time && movie.episode_run_time[0]) {
      return `${movie.episode_run_time[0]}m/ep`;
    }
    return null;
  };

  const getRating = () => {
    if (movie.rating) {
      return (movie.rating * 10).toFixed(0) + '%';
    }
    if (movie.vote_average) {
      return (movie.vote_average * 10).toFixed(0) + '%';
    }
    return null;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  // Se tiver um filme semelhante selecionado, renderiza modal recursivo
  if (selectedSimilarMovie) {
    return (
      <MovieDetailsModal 
        movie={selectedSimilarMovie} 
        onClose={handleCloseSimilarModal}
      />
    );
  }

  if (!movie) return null;

  return (
    <AnimatePresence>
      <motion.div 
        className="netflix-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div 
          className="netflix-modal-content"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close Button */}
          <button className="netflix-modal-close" onClick={onClose}>
            <X size={24} />
          </button>

          {/* Hero Video Section - 100% Width */}
          <div className="netflix-modal-hero">
            {isSeries ? (
              // Série: mostrar backdrop da série
              <div className="netflix-backdrop-container">
                <img 
                  src={getBackdropImageUrl(movie.backdrop_path, getImageUrl(movie.poster_path))} 
                  alt={movie.title || movie.name}
                  className="netflix-backdrop-img"
                />
                <div className="netflix-backdrop-gradient" />
              </div>
            ) : trailer ? (
              <div className="netflix-video-container">
                <iframe
                  ref={iframeRef}
                  src={`https://www.youtube.com/embed/${trailer.key}?autoplay=1&mute=1&controls=0&rel=0&modestbranding=1&loop=1&playlist=${trailer.key}&enablejsapi=1`}
                  title="Trailer"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
                
                {/* Gradient Overlay */}
                <div className="netflix-video-gradient" />
                
                {/* Mute Toggle */}
                <button 
                  className="netflix-mute-btn"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                </button>
              </div>
            ) : (
              <div className="netflix-backdrop-container">
                <img 
                  src={getBackdropUrl(movie.backdrop_path)} 
                  alt={movie.title || movie.name}
                  className="netflix-backdrop-img"
                />
                <div className="netflix-backdrop-gradient" />
              </div>
            )}

            {/* Hero Info Overlay */}
            <div className="netflix-hero-info">
              <motion.h1 
                className="netflix-hero-title"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                {movie.title || movie.name}
              </motion.h1>

              {/* Meta Info */}
              <div className="netflix-meta">
                {getRating() && <span className="netflix-rating">{getRating()} Match</span>}
                <span className="netflix-year">{getYear()}</span>
                {getRuntime() && <span className="netflix-runtime">{getRuntime()}</span>}
                <span className="netflix-hd">HD</span>
              </div>

              {/* Actions */}
              <div className="netflix-actions">
                <button className="btn-primary netflix-btn-play" onClick={handleWatchNow}>
                  <Play size={24} fill="currentColor" />
                  <span>{isSeries ? 'Assistir S01E01' : 'Assistir'}</span>
                </button>
                
                <button 
                  className={`btn-secondary netflix-btn-list ${inList ? 'in-list' : ''}`}
                  onClick={handleToggleList}
                >
                  {inList ? <Check size={24} /> : <Plus size={24} />}
                  <span>{inList ? 'Na Minha Lista' : 'Minha Lista'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Content Body */}
          <div className="netflix-modal-body">
            {/* Main Info */}
            <div className="netflix-info-section">
              <div className="netflix-left-col">
                <p className="netflix-overview">{movie.overview || "Nenhuma descrição disponível para este título."}</p>
              </div>

              <div className="netflix-right-col">
                {!isSeries && cast.length > 0 && (
                  <div className="netflix-info-row">
                    <span className="netflix-label">Elenco:</span>
                    <span className="netflix-value">{cast.slice(0, 3).map(c => c.name).join(', ')}{cast.length > 3 ? '...' : ''}</span>
                  </div>
                )}
                
                {getGenres() && (
                  <div className="netflix-info-row">
                    <span className="netflix-label">Gêneros:</span>
                    <span className="netflix-value">{getGenres()}</span>
                  </div>
                )}

                {(movie.vote_average > 0 || movie.rating > 0) && (
                  <div className="netflix-info-row">
                    <span className="netflix-label">Avaliação:</span>
                    <span className="netflix-value">
                      <Star size={14} className="netflix-star" />
                      {(movie.vote_average || movie.rating).toFixed(1)}/10
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Séries: Temporadas e Episódios */}
            {isSeries && seriesData?.seasons && (
              <div className="netflix-episodes-section">
                <div className="netflix-seasons-header">
                  <h3 className="netflix-section-title">Episódios</h3>
                  
                  {/* Season Selector */}
                  {seriesData.seasons.length > 1 && (
                    <div className="netflix-season-selector">
                      <select 
                        value={selectedSeasonNumber || ''}
                        onChange={(e) => {
                          const seasonNumber = parseInt(e.target.value);
                          console.log('[Season Change] Selected:', seasonNumber);
                          setSelectedSeasonNumber(seasonNumber);
                          const season = seriesData.seasons.find(s => s.season_number === seasonNumber);
                          if (season) {
                            console.log('[Season Change] Found season with', season.episodes?.length, 'episodes');
                            setSelectedSeason(season);
                          }
                        }}
                        className="netflix-season-dropdown"
                      >
                        {seriesData.seasons.map(season => (
                          <option key={season.season_number} value={season.season_number}>
                            Temporada {season.season_number} ({season.episodes?.length || 0} eps)
                          </option>
                        ))}
                      </select>
                      <ChevronDown size={16} className="netflix-dropdown-icon" />
                    </div>
                  )}
                </div>

                {/* Debug info */}
                {selectedSeason && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px' }}>
                    Temporada {selectedSeason.season_number} • {selectedSeason.episodes?.length || 0} episódios
                  </div>
                )}

                {/* Episodes List */}
                {selectedSeason?.episodes && selectedSeason.episodes.length > 0 ? (
                  <div className="netflix-episodes-list">
                    {selectedSeason.episodes.map((episode, index) => (
                      <div 
                        key={episode.id}
                        className="netflix-episode-item"
                        onClick={() => handleWatchEpisode(episode)}
                      >
                        <div className="netflix-episode-number">{index + 1}</div>
                        <div className="netflix-episode-image">
                          {episode.still_path ? (
                            <img src={episode.still_path} alt={episode.title} />
                          ) : (
                            <div className="netflix-episode-placeholder">
                              <Play size={24} />
                            </div>
                          )}
                          <div className="netflix-episode-play-overlay">
                            <Play size={32} fill="white" />
                          </div>
                        </div>
                        <div className="netflix-episode-info">
                          <div className="netflix-episode-header">
                            <h4 className="netflix-episode-title">{episode.title}</h4>
                            {episode.duration > 0 && (
                              <span className="netflix-episode-duration">{formatDuration(episode.duration)}</span>
                            )}
                          </div>
                          <p className="netflix-episode-overview">
                            {episode.overview || "Nenhuma descrição disponível."}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : selectedSeason ? (
                  <div className="netflix-episodes-list" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Nenhum episódio disponível para esta temporada.
                  </div>
                ) : null}

                {loadingSeries && (
                  <div className="netflix-loading">
                    <div className="netflix-spinner"></div>
                    <p>Carregando episódios...</p>
                  </div>
                )}
              </div>
            )}

            {/* Similar Movies */}
            {!isSeries && similar.length > 0 && (
              <div className="netflix-similar-section">
                <h3 className="netflix-section-title">Títulos Semelhantes</h3>
                <div className="netflix-similar-grid">
                  {similar.map((simMovie) => (
                    <div 
                      key={simMovie.id} 
                      className="netflix-similar-card"
                      onClick={() => handleSimilarClick(simMovie)}
                    >
                      <img 
                        src={getPosterUrl(simMovie.poster_path)} 
                        alt={simMovie.title || simMovie.name}
                        className="netflix-similar-poster"
                      />
                      <div className="netflix-similar-info">
                        <h4>{simMovie.title || simMovie.name}</h4>
                        <span className="netflix-similar-meta">
                          {(simMovie.release_date || simMovie.first_air_date || '').substring(0, 4)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default MovieDetailsModal;
