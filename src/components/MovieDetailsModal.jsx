import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, Plus, Check, Star, Clock, Calendar, Globe, Volume2, VolumeX } from 'lucide-react';
import { useTMDB, getBackdropUrl, genreMap } from '../hooks/useTMDB';
import { useMyList } from '../hooks/useDatabase';
import { useNavigate } from 'react-router-dom';
import '../styles/MovieDetailsModal.css';

const MovieDetailsModal = ({ movie, onClose }) => {
  const [trailer, setTrailer] = useState(null);
  const [cast, setCast] = useState([]);
  const [inList, setInList] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const iframeRef = React.useRef(null);
  const { fetchData } = useTMDB();
  const { addMovie, removeMovie, checkIsInList } = useMyList();
  const navigate = useNavigate();

  useEffect(() => {
    const loadDetails = async () => {
      // Check if in list
      const isMovieInList = await checkIsInList(movie.id);
      setInList(isMovieInList);

      // Fetch videos (trailers)
      const videosData = await fetchData(`/movie/${movie.id}/videos`);
      if (videosData?.results) {
        const officialTrailer = videosData.results.find(
          v => v.type === 'Trailer' && (v.site === 'YouTube' || v.site === 'Vimeo')
        );
        setTrailer(officialTrailer);
      }

      // Fetch credits (cast)
      const creditsData = await fetchData(`/movie/${movie.id}/credits`);
      if (creditsData?.cast) {
        setCast(creditsData.cast.slice(0, 5));
      }
    };

    if (movie?.id) loadDetails();
  }, [movie, fetchData, checkIsInList]);

  // Handle Mute/Unmute without reloading the iframe
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
    navigate(`/watch/${movie.id}`, { state: { movie } });
    onClose();
  };

  const handleToggleList = async () => {
    if (inList) {
      const success = await removeMovie(movie.id);
      if (success) setInList(false);
    } else {
      const success = await addMovie(movie);
      if (success) setInList(true);
    }
  };

  const getYear = () => {
    const dateStr = movie.release_date || movie.first_air_date;
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return isNaN(date.getFullYear()) ? dateStr.split('-')[0] : date.getFullYear();
  };

  const getGenres = () => {
    if (movie.genres && movie.genres.length > 0) {
      return movie.genres.map(g => g.name).join(', ');
    }
    if (movie.genre_ids && movie.genre_ids.length > 0) {
      return movie.genre_ids.map(id => genreMap[id] || id).join(', ');
    }
    return '';
  };

  if (!movie) return null;

  return (
    <motion.div 
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div 
        className="modal-content"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        <div className="modal-header">
          {trailer ? (
            <div className="trailer-container">
              <iframe
                ref={iframeRef}
                src={`https://www.youtube.com/embed/${trailer.key}?autoplay=1&mute=1&controls=0&rel=0&modestbranding=1&loop=1&playlist=${trailer.key}&enablejsapi=1`}
                title="Trailer"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
              
              <button 
                className="modal-mute-toggle"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}
              </button>
            </div>
          ) : (
            <div className="modal-backdrop-fallback">
              <img src={getBackdropUrl(movie.backdrop_path)} alt={movie.title} />
            </div>
          )}
          
          <div className="trailer-overlay"></div>

          <div className="modal-header-info">
            <h2 className="modal-title">{movie.title || movie.name}</h2>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleWatchNow}>
                <Play size={20} fill="currentColor" />
                ASSISTIR AGORA
              </button>
              <button 
                className={`btn-secondary ${inList ? 'active' : ''}`}
                onClick={handleToggleList}
              >
                {inList ? <Check size={20} /> : <Plus size={20} />}
                {inList ? 'NA MINHA LISTA' : 'MINHA LISTA'}
              </button>
            </div>
          </div>
        </div>

        <div className="modal-body">
          <div className="modal-main-info">
            <div className="info-row">
              <span className="info-year">{getYear()}</span>
            </div>
            
            <p className="modal-overview">{movie.overview || "Nenhuma descrição disponível para este título."}</p>
          </div>

          <div className="modal-aside-info">
            {cast.length > 0 && (
              <div className="info-group">
                <span className="info-label">Elenco:</span>
                <span className="info-value">{cast.map(c => c.name).join(', ')}</span>
              </div>
            )}
            
            {getGenres() && (
              <div className="info-group">
                <span className="info-label">Gêneros:</span>
                <span className="info-value">
                  {getGenres()}
                </span>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default MovieDetailsModal;
