import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle, 
  ExternalLink,
  Play,
  Shield
} from 'lucide-react';
import '../styles/AdminPage.css';

const LinkVerifier = () => {
  const [movies, setMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [fixing, setFixing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMovies();
  }, []);

  const fetchMovies = async () => {
    try {
      const response = await fetch('http://127.0.0.1:3000/api/catalog?limit=1000');
      const data = await response.json();
      if (data.results) {
        // Only show movies with links (not NOT_FOUND)
        const withLinks = data.results.filter(m => 
          m.embedUrl && m.embedUrl !== 'NOT_FOUND'
        );
        setMovies(withLinks);
      }
    } catch (error) {
      console.error('Error fetching movies:', error);
    }
  };

  const verifyMovie = async (movie) => {
    setSelectedMovie(movie);
    setVerifying(true);
    setVerifyResult(null);

    try {
      const response = await fetch('http://127.0.0.1:3000/api/verify-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: movie.title,
          currentUrl: movie.embedUrl
        })
      });

      const result = await response.json();
      setVerifyResult(result);
    } catch (error) {
      setVerifyResult({ error: error.message });
    } finally {
      setVerifying(false);
    }
  };

  const fixMovie = async () => {
    if (!selectedMovie || !verifyResult?.scraped_result?.video_url) return;

    setFixing(true);
    try {
      const response = await fetch('http://127.0.0.1:3000/api/fix-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: selectedMovie.title,
          tmdbId: selectedMovie.id
        })
      });

      const result = await response.json();
      
      if (result.success) {
        alert(`✅ Link corrigido com sucesso!\nNovo link: ${result.video_url}`);
        fetchMovies(); // Refresh list
        setVerifyResult(null);
        setSelectedMovie(null);
      } else {
        alert(`❌ Erro: ${result.error}`);
      }
    } catch (error) {
      alert(`❌ Erro: ${error.message}`);
    } finally {
      setFixing(false);
    }
  };

  return (
    <div className="admin-page">
      <header className="admin-header">
        <button className="back-btn" onClick={() => navigate('/admin')}>
          <ArrowLeft size={20} />
          Voltar
        </button>
        <h1><Shield size={24} /> Verificador de Links</h1>
        <button className="refresh-btn" onClick={fetchMovies}>
          <RefreshCw size={18} />
          Atualizar
        </button>
      </header>

      <div style={{ 
        background: 'rgba(255,255,255,0.05)', 
        padding: '20px', 
        borderRadius: '12px',
        marginBottom: '30px'
      }}>
        <h3 style={{ marginTop: 0 }}>Como funciona:</h3>
        <ol style={{ lineHeight: '1.8', margin: 0 }}>
          <li>Selecione um filme da lista abaixo</li>
          <li>O sistema vai buscar o link atual no Opera Topzera</li>
          <li>Se o link estiver errado, você pode corrigi-lo com um clique</li>
          <li>Filmes marcados com 🟢 já foram verificados</li>
        </ol>
      </div>

      {selectedMovie && (
        <div style={{ 
          background: 'rgba(229, 9, 20, 0.1)', 
          border: '2px solid #e50914',
          padding: '20px', 
          borderRadius: '12px',
          marginBottom: '30px'
        }}>
          <h3 style={{ marginTop: 0 }}>Verificando: {selectedMovie.title}</h3>
          
          {verifying ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <RefreshCw className="spin" size={24} />
              <span>Buscando no Opera Topzera...</span>
            </div>
          ) : verifyResult ? (
            <div>
              {verifyResult.error ? (
                <div style={{ color: '#ff4444' }}>
                  <AlertTriangle size={20} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                  Erro: {verifyResult.error}
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: '15px' }}>
                    <strong>Link atual no banco:</strong><br/>
                    <code style={{ 
                      background: 'rgba(0,0,0,0.3)', 
                      padding: '5px 10px', 
                      borderRadius: '4px',
                      fontSize: '0.9rem'
                    }}>
                      {verifyResult.current_url}
                    </code>
                  </div>

                  {verifyResult.scraped_result?.success ? (
                    <div>
                      <div style={{ marginBottom: '15px' }}>
                        <strong>Link real no Opera:</strong><br/>
                        <code style={{ 
                          background: 'rgba(0,0,0,0.3)', 
                          padding: '5px 10px', 
                          borderRadius: '4px',
                          fontSize: '0.9rem',
                          color: verifyResult.is_correct ? '#4caf50' : '#ff4444'
                        }}>
                          {verifyResult.scraped_result.video_url}
                        </code>
                      </div>

                      <div style={{ marginBottom: '15px' }}>
                        <strong>Título encontrado:</strong> {verifyResult.scraped_result.scraped_title}<br/>
                        <strong>Similaridade:</strong> {(verifyResult.scraped_result.similarity * 100).toFixed(1)}%<br/>
                        <strong>ID do vídeo:</strong> {verifyResult.scraped_result.video_id}
                      </div>

                      {verifyResult.is_correct ? (
                        <div style={{ 
                          background: 'rgba(76, 175, 80, 0.2)', 
                          padding: '15px', 
                          borderRadius: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px'
                        }}>
                          <CheckCircle size={24} color="#4caf50" />
                          <span>✅ Link está correto!</span>
                        </div>
                      ) : (
                        <div>
                          <div style={{ 
                            background: 'rgba(255, 68, 68, 0.2)', 
                            padding: '15px', 
                            borderRadius: '8px',
                            marginBottom: '15px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px'
                          }}>
                            <AlertTriangle size={24} color="#ff4444" />
                            <span>🚨 Link incorreto detectado!</span>
                          </div>
                          
                          <button
                            onClick={fixMovie}
                            disabled={fixing}
                            style={{
                              background: '#e50914',
                              color: '#fff',
                              border: 'none',
                              padding: '12px 24px',
                              borderRadius: '8px',
                              cursor: fixing ? 'not-allowed' : 'pointer',
                              fontSize: '1rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              opacity: fixing ? 0.7 : 1
                            }}
                          >
                            {fixing ? (
                              <>
                                <RefreshCw className="spin" size={18} />
                                Corrigindo...
                              </>
                            ) : (
                              <>
                                <CheckCircle size={18} />
                                Corrigir Link Agora
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ color: '#ff9800' }}>
                      <AlertTriangle size={20} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                      Não foi possível extrair link do Opera: {verifyResult.scraped_result?.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      <div className="movies-list">
        <div className="movies-table-header" style={{ gridTemplateColumns: '2fr 2fr 120px' }}>
          <span>Filme</span>
          <span>Link Atual</span>
          <span>Ação</span>
        </div>
        
        {movies.map((movie) => (
          <div 
            key={movie.id} 
            className="movie-row"
            style={{ 
              gridTemplateColumns: '2fr 2fr 120px',
              background: selectedMovie?.id === movie.id ? 'rgba(229, 9, 20, 0.1)' : undefined
            }}
          >
            <div className="movie-info">
              <img 
                src={`https://image.tmdb.org/t/p/w92${movie.poster_path}`} 
                alt={movie.title}
                onError={(e) => e.target.style.display = 'none'}
              />
              <span className="movie-title">{movie.title}</span>
            </div>
            
            <div className="link-cell">
              <code style={{ fontSize: '0.8rem' }}>
                {movie.embedUrl.length > 50 
                  ? movie.embedUrl.substring(0, 50) + '...' 
                  : movie.embedUrl}
              </code>
            </div>
            
            <div>
              <button
                onClick={() => verifyMovie(movie)}
                disabled={verifying || fixing}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  color: '#fff',
                  border: '1px solid rgba(255,255,255,0.2)',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: (verifying || fixing) ? 'not-allowed' : 'pointer',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
              >
                <Shield size={14} />
                Verificar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LinkVerifier;
