import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, CheckCircle, Clock, Youtube, Tv } from 'lucide-react';
import { getPosterUrl } from '../hooks/useTMDB';

const MovieCard = ({ movie, index, onClick, isAvailable }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Detectar se é série da nossa API (tem opera_id)
  const isLocalSeries = movie.opera_id || movie.isLocalSeries;
  
  // Detectar tipo de link
  const getLinkStatus = () => {
    // Se for série da nossa API, sempre está disponível
    if (isLocalSeries) {
      return { type: 'series', icon: <Tv size={14} />, label: 'Série', color: '#e50914' };
    }
    
    const embedUrl = movie.embedUrl || movie.embed_url;
    
    if (!embedUrl || embedUrl === 'NOT_FOUND') {
      return { type: 'pending', icon: <Clock size={14} />, label: 'Pendente', color: '#ff9800' };
    }
    
    if (embedUrl.includes('youtube.com') || embedUrl.includes('youtu.be')) {
      return { type: 'youtube', icon: <Youtube size={14} />, label: 'YouTube (Errado)', color: '#ff4444' };
    }
    
    if (embedUrl.includes('jt0x.com')) {
      return { type: 'verified', icon: <CheckCircle size={14} />, label: 'Opera OK', color: '#4caf50' };
    }
    
    return { type: 'available', icon: <CheckCircle size={14} />, label: 'Disponível', color: '#4caf50' };
  };
  
  const linkStatus = getLinkStatus();
  
  // Obter URL do poster (séries da API já vêm com URL completa)
  const getPosterImage = () => {
    if (movie.poster_path && movie.poster_path.startsWith('http')) {
      return movie.poster_path;
    }
    return getPosterUrl(movie.poster_path);
  };
  
  // Obter rating (TMDB usa vote_average, nossa API usa rating)
  const getRating = () => {
    return movie.vote_average || movie.rating || 0;
  };
  
  return (
    <motion.div
      className="movie-card"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.5 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onClick(movie)}
    >
      <div className="movie-card-inner">
        <img 
          src={getPosterImage()} 
          alt={movie.title || movie.name}
          className="movie-poster"
          loading="lazy"
        />
        
        {/* Hover clean - sem overlay */}
      </div>
    </motion.div>
  );
};

export default MovieCard;
