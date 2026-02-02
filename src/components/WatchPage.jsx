import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Play, Info, Star, Calendar, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getVideoLink, saveVideoLink } from '../db';
import { useTMDB, getBackdropUrl } from '../hooks/useTMDB';

const WatchPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { fetchData } = useTMDB();
  
  const [movieDetails, setMovieDetails] = useState(location.state?.movie || null);
  const [embedUrl, setEmbedUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("Iniciando...");

  useEffect(() => {
    const init = async () => {
        setLoading(true);
        setError(null);

        try {
            let currentMovie = movieDetails;
            if (!currentMovie) {
                setStatus("Obtendo detalhes...");
                const data = await fetchData(`/movie/${id}?language=pt-BR`);
                if (data && data.id) {
                    currentMovie = data;
                    setMovieDetails(data);
                } else {
                    throw new Error("Filme não encontrado.");
                }
            }

            if (currentMovie && currentMovie.embedUrl && currentMovie.embedUrl !== "NOT_FOUND") {
                setEmbedUrl(currentMovie.embedUrl);
                setLoading(false);
                return;
            } else if (currentMovie?.embedUrl === "NOT_FOUND") {
                 setError("Este título está sendo processado e estará disponível em breve.");
                 setLoading(false);
                 return;
            }

            setStatus("Buscando player...");
            const cachedLink = await getVideoLink(id);
            if (cachedLink && cachedLink !== "NOT_FOUND") {
                setEmbedUrl(cachedLink);
                setLoading(false);
                return;
            }

            setStatus("Preparando stream...");
            const title = currentMovie.title || currentMovie.name;
            const year = (currentMovie.release_date || currentMovie.first_air_date)?.split('-')[0];

            const response = await fetch('http://127.0.0.1:3000/api/get-embed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, tmdbId: id, year }),
            });

            const data = await response.json();
            if (response.ok && data.embedUrl && data.embedUrl !== "NOT_FOUND") {
                setEmbedUrl(data.embedUrl);
                await saveVideoLink(id, data.embedUrl);
            } else {
                const isNotFound = data.embedUrl === "NOT_FOUND";
                setError(isNotFound ? "Este título está sendo processado." : (data.error || "Link não disponível no momento."));
            }
        } catch (err) {
            setError("Erro ao conectar com o serviço.");
        } finally {
            setLoading(false);
        }
    };

    if (id) init();
  }, [id, fetchData]);

  return (
    <div className="watch-page">
      {/* Dynamic Background */}
      <div className="watch-backdrop">
        <img src={getBackdropUrl(movieDetails?.backdrop_path)} alt="" />
        <div className="backdrop-overlay" />
      </div>

      <header className="watch-header">
        <motion.button 
          className="back-btn" 
          onClick={() => navigate(-1)}
          whileHover={{ x: -5 }}
          whileTap={{ scale: 0.95 }}
        >
          <ArrowLeft size={20} />
          <span>Voltar</span>
        </motion.button>
        
        {movieDetails && (
          <div className="watch-title-info">
            <h1>{movieDetails.title || movieDetails.name}</h1>
            <div className="header-meta">
               <span className="rating"><Star size={14} fill="#ffd700" color="#ffd700" /> {movieDetails.vote_average?.toFixed(1)}</span>
               <span className="dot">•</span>
               <span>{(movieDetails.release_date || movieDetails.first_air_date)?.substring(0, 4)}</span>
            </div>
          </div>
        )}
      </header>

      <main className="player-section">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div 
              key="loading"
              className="player-state-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="loading-content">
                <div className="premium-loader" />
                <h2>{status}</h2>
                <p>Configurando a melhor qualidade para você.</p>
              </div>
            </motion.div>
          ) : error ? (
            <motion.div 
              key="error"
              className="player-state-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="error-content">
                <AlertCircle size={48} color="#ff4d4d" />
                <h2>Não foi possível carregar</h2>
                <p>{error}</p>
                <button onClick={() => navigate(-1)} className="btn-retry">Escolher outro filme</button>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="player"
              className="iframe-wrapper"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <iframe
                src={embedUrl}
                title={movieDetails?.title || "Player"}
                className="video-player"
                allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <style jsx>{`
        .watch-page {
          position: relative;
          min-height: 100vh;
          background: #050505;
          color: #fff;
          overflow: hidden;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        .watch-backdrop {
          position: fixed;
          inset: 0;
          z-index: 0;
        }

        .watch-backdrop img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          filter: blur(40px) brightness(0.3);
          transform: scale(1.1);
        }

        .backdrop-overlay {
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at center, transparent 0%, #050505 100%);
        }

        .watch-header {
          position: relative;
          z-index: 10;
          padding: 24px 40px;
          display: flex;
          align-items: center;
          gap: 24px;
          background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, transparent 100%);
        }

        .back-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          padding: 10px 20px;
          border-radius: 100px;
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          backdrop-filter: blur(20px);
          font-weight: 500;
          transition: all 0.2s;
        }

        .back-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.3);
        }

        .watch-title-info h1 {
          font-size: 1.25rem;
          margin: 0;
          font-weight: 600;
          letter-spacing: -0.02em;
        }

        .header-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
          margin-top: 4px;
        }

        .rating {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #ffd700;
        }

        .player-section {
          position: relative;
          z-index: 5;
          width: 100%;
          height: calc(100vh - 100px);
          padding: 0 40px 40px;
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .iframe-wrapper {
          width: 100%;
          height: 100%;
          max-width: 1600px;
          aspect-ratio: 16 / 9;
          border-radius: 12px;
          overflow: hidden;
          background: #000;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .video-player {
          width: 100%;
          height: 100%;
          border: none;
        }

        .player-state-overlay {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .loading-content h2, .error-content h2 {
          font-size: 1.5rem;
          margin: 24px 0 8px;
        }

        .loading-content p, .error-content p {
          color: rgba(255, 255, 255, 0.6);
        }

        .premium-loader {
          width: 48px;
          height: 48px;
          border: 3px solid rgba(255, 255, 255, 0.1);
          border-top-color: #3498db;
          border-radius: 50%;
          animation: spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }

        .btn-retry {
          margin-top: 24px;
          background: #ff4d4d;
          color: #fff;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .btn-retry:hover {
          transform: scale(1.05);
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .watch-header { padding: 16px; }
          .player-section { padding: 0 16px 16px; height: calc(100vh - 80px); }
          .watch-title-info { display: none; }
        }
      `}</style>
    </div>
  );
};

export default WatchPage;
