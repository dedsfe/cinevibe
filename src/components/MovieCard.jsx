import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, CheckCircle, Clock, Youtube } from 'lucide-react';
import { getPosterUrl } from '../hooks/useTMDB';

const MovieCard = ({ movie, index, onClick, isAvailable }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Detectar tipo de link
  const getLinkStatus = () => {
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
          src={getPosterUrl(movie.poster_path)} 
          alt={movie.title || movie.name}
          className="movie-poster"
          loading="lazy"
        />
        
        <AnimatePresence>
          {isHovered && (
            <motion.div 
              className="movie-card-overlay"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
            >
              <div className="movie-card-info">
                <h4 className="movie-title">{movie.title || movie.name}</h4>
                
                <div className="card-status-row">
                  <div 
                    className={`mini-status ${linkStatus.type}`}
                    style={{ color: linkStatus.color }}
                  >
                    {linkStatus.icon}
                    <span>{linkStatus.label === 'Disponível' ? 'HD' : linkStatus.label}</span>
                  </div>
                  
                  <div className="movie-rating">
                    <Star size={12} fill="#ffd700" color="#ffd700" />
                    <span>{movie.vote_average?.toFixed(1)}</span>
                  </div>
                </div>

              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default MovieCard;
