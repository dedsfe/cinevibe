import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Youtube, 
  RefreshCw, 
  Search,
  ArrowLeft,
  Database,
  Shield
} from 'lucide-react';
import '../styles/AdminPage.css';

const AdminPage = () => {
  const [movies, setMovies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch catalog from backend
      const response = await fetch('http://127.0.0.1:8080/api/catalog?limit=1000');
      const data = await response.json();
      
      if (data.results) {
        setMovies(data.results);
        calculateStats(data.results);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (moviesData) => {
    const stats = {
      total: moviesData.length,
      verified: 0,
      pending: 0,
      youtube: 0,
      other: 0
    };

    moviesData.forEach(movie => {
      const url = movie.embedUrl;
      
      if (!url || url === 'NOT_FOUND') {
        stats.pending++;
      } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
        stats.youtube++;
      } else if (url.includes('jt0x.com')) {
        stats.verified++;
      } else {
        stats.other++;
      }
    });

    setStats(stats);
  };

  const getMovieStatus = (movie) => {
    const url = movie.embedUrl;
    
    if (!url || url === 'NOT_FOUND') {
      return { 
        type: 'pending', 
        label: 'Pendente', 
        color: '#ff9800',
        icon: <Clock size={16} />
      };
    }
    
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      return { 
        type: 'youtube', 
        label: 'YouTube (Incorreto)', 
        color: '#ff4444',
        icon: <Youtube size={16} />
      };
    }
    
    if (url.includes('jt0x.com')) {
      return { 
        type: 'verified', 
        label: 'Opera Verificado', 
        color: '#4caf50',
        icon: <CheckCircle size={16} />
      };
    }
    
    return { 
      type: 'other', 
      label: 'Outro', 
      color: '#2196f3',
      icon: <CheckCircle size={16} />
    };
  };

  const filteredMovies = movies.filter(movie => {
    const status = getMovieStatus(movie);
    
    // Filter by status
    if (filter !== 'all' && status.type !== filter) {
      return false;
    }
    
    // Filter by search
    if (searchTerm && !movie.title.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    
    return true;
  });

  return (
    <div className="admin-page">
      <header className="admin-header">
        <button className="back-btn" onClick={() => navigate('/')}>
          <ArrowLeft size={20} />
          Voltar
        </button>
        <h1><Shield size={24} /> Painel de Administração</h1>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          <RefreshCw size={18} className={loading ? 'spin' : ''} />
          Atualizar
        </button>
      </header>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card total">
            <Database size={24} />
            <div className="stat-info">
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total de Filmes</span>
            </div>
          </div>
          
          <div className="stat-card verified">
            <CheckCircle size={24} />
            <div className="stat-info">
              <span className="stat-value">{stats.verified}</span>
              <span className="stat-label">✅ Verificados (Opera)</span>
            </div>
          </div>
          
          <div className="stat-card pending">
            <Clock size={24} />
            <div className="stat-info">
              <span className="stat-value">{stats.pending}</span>
              <span className="stat-label">⏳ Pendentes</span>
            </div>
          </div>
          
          <div className="stat-card youtube">
            <AlertTriangle size={24} />
            <div className="stat-info">
              <span className="stat-value">{stats.youtube}</span>
              <span className="stat-label">⚠️ YouTube (Errados)</span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        marginBottom: '30px',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => navigate('/verify-links')}
          style={{
            background: '#e50914',
            color: '#fff',
            border: 'none',
            padding: '15px 30px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontWeight: '600'
          }}
        >
          <Shield size={20} />
          Verificar Links Manualmente
        </button>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-box">
          <Search size={18} />
          <input 
            type="text" 
            placeholder="Buscar filme..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="filter-buttons">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            Todos ({stats?.total || 0})
          </button>
          <button 
            className={filter === 'verified' ? 'active' : ''}
            onClick={() => setFilter('verified')}
          >
            ✅ Verificados ({stats?.verified || 0})
          </button>
          <button 
            className={filter === 'pending' ? 'active' : ''}
            onClick={() => setFilter('pending')}
          >
            ⏳ Pendentes ({stats?.pending || 0})
          </button>
          <button 
            className={filter === 'youtube' ? 'active' : ''}
            onClick={() => setFilter('youtube')}
          >
            ⚠️ YouTube ({stats?.youtube || 0})
          </button>
        </div>
      </div>

      {/* Movies List */}
      <div className="movies-list">
        {loading ? (
          <div className="loading">Carregando...</div>
        ) : filteredMovies.length === 0 ? (
          <div className="empty">Nenhum filme encontrado</div>
        ) : (
          <>
            <div className="movies-table-header">
              <span>Filme</span>
              <span>Status</span>
              <span>Link</span>
              <span>TMDB ID</span>
            </div>
            
            {filteredMovies.map((movie) => {
              const status = getMovieStatus(movie);
              return (
                <div key={movie.id} className={`movie-row ${status.type}`}>
                  <div className="movie-info">
                    <img 
                      src={`https://image.tmdb.org/t/p/w92${movie.poster_path}`} 
                      alt={movie.title}
                      onError={(e) => e.target.style.display = 'none'}
                    />
                    <span className="movie-title">{movie.title}</span>
                  </div>
                  
                  <div className="status-cell">
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: status.color }}
                    >
                      {status.icon}
                      {status.label}
                    </span>
                  </div>
                  
                  <div className="link-cell">
                    {movie.embedUrl && movie.embedUrl !== 'NOT_FOUND' ? (
                      <a 
                        href={movie.embedUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="link-preview"
                        title={movie.embedUrl}
                      >
                        {movie.embedUrl.length > 40 
                          ? movie.embedUrl.substring(0, 40) + '...' 
                          : movie.embedUrl}
                      </a>
                    ) : (
                      <span className="no-link">Sem link</span>
                    )}
                  </div>
                  
                  <div className="tmdb-cell">
                    <a 
                      href={`https://www.themoviedb.org/movie/${movie.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {movie.id}
                    </a>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminPage;
