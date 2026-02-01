import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Loader } from 'lucide-react';
import { getVideoLink, saveVideoLink } from '../db';
import { useTMDB } from '../hooks/useTMDB';

const WatchPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { fetchData } = useTMDB();
  
  // State for movie details
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
            // 1. Resolve Movie Details if missing
            let currentMovie = movieDetails;
            if (!currentMovie) {
                setStatus("Obtendo detalhes do filme...");
                try {
                    // Try fetch as movie first, then tv if needed (or just assume movie for now based on context)
                    // Better: try both or just movie. API differentiates by endpoint usually.
                    // For now, let's assume it's a movie since we clicked a movie.
                    const data = await fetchData(`/movie/${id}?language=pt-BR`);
                    if (data && data.id) {
                        currentMovie = data;
                        setMovieDetails(data);
                    } else {
                         // Fallback try TV if movie fails? Or just error.
                         throw new Error("Filme não encontrado no TMDB.");
                    }
                } catch (e) {
                    console.error("Erro ao buscar detalhes:", e);
                    setError("Erro ao carregar informações do filme.");
                    setLoading(false);
                    return;
                }
            }

            // 2. Check Local DB
            setStatus("Verificando arquivos salvos...");
            const cachedLink = await getVideoLink(id);
            if (cachedLink) {
                console.log("Using locally cached link:", cachedLink);
                setEmbedUrl(cachedLink);
                setLoading(false);
                return;
            }

            // 3. Fetch from Backend
            setStatus("Buscando link seguro na web (isso pode levar alguns segundos)...");
            
            const title = currentMovie.title || currentMovie.name;
            const year = (currentMovie.release_date || currentMovie.first_air_date)?.split('-')[0];

            console.log("Searching for:", title, year);

            const response = await fetch('http://127.0.0.1:5000/api/get-embed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    tmdbId: id,
                    year: year
                }),
            });

            const data = await response.json();

            if (response.ok && data.embedUrl) {
                setEmbedUrl(data.embedUrl);
                await saveVideoLink(id, data.embedUrl);
            } else {
                setError(data.error || "Filme não encontrado.");
            }

        } catch (err) {
            console.error(err);
            setError("Erro de conexão com o servidor. Tente novamente.");
        } finally {
            setLoading(false);
        }
    };

    if (id) {
        init();
    }
  }, [id, fetchData]); // Removed movie dependency to avoid loops if we update it

  return (
    <div className="watch-page">
      <button className="back-btn" onClick={() => navigate(-1)}>
        <ArrowLeft size={24} /> Voltar
      </button>

      <div className="player-container">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <h2>{status}</h2>
            <p>Por favor, aguarde enquanto localizamos o player.</p>
          </div>
        ) : error ? (
            <div className="error-state">
                <AlertCircle size={48} color="#e74c3c" />
                <h2>Ops!</h2>
                <p>{error}</p>
                <button onClick={() => navigate(-1)} className="retry-btn">Voltar para Início</button>
            </div>
        ) : (
          <iframe
            src={embedUrl}
            title={movie.title || "Movie Player"}
            className="video-iframe"
            allowFullScreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          />
        )}
      </div>

      <style jsx>{`
        .watch-page {
          min-height: 100vh;
          background: #000;
          color: #fff;
          display: flex;
          flex-direction: column;
        }
        .back-btn {
          position: absolute;
          top: 20px;
          left: 20px;
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: #fff;
          padding: 10px 20px;
          border-radius: 30px;
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          backdrop-filter: blur(10px);
          z-index: 10;
          transition: background 0.2s;
        }
        .back-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        .player-container {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%;
          height: 100vh;
        }
        .video-iframe {
          width: 100%;
          height: 100%;
          border: none;
        }
        .loading-state, .error-state {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            max-width: 400px;
            padding: 20px;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        .retry-btn {
            margin-top: 20px;
            background: #e74c3c;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default WatchPage;
