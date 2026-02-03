import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Terminal, Activity, CheckCircle, AlertCircle, Play } from 'lucide-react';

const ScraperStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8080/api/scraper/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch status:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="status-page">
        <div className="status-container">
          <h2>Carregando Status...</h2>
        </div>
      </div>
    );
  }

  const { is_running, current_movie, progress, logs } = status || {};
  const percent = progress?.total ? Math.round((progress.current / progress.total) * 100) : 0;

  return (
    <div className="status-page">
        <div className="status-header">
            <h1><Activity className="icon" /> Painel do Scraper</h1>
            <a href="/" className="back-link">Voltar ao Site</a>
        </div>

      <div className="status-container">
        {/* Main Status Card */}
        <motion.div 
            className="status-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
          <div className="status-indicator">
            <div className={`indicator-dot ${is_running ? 'running' : 'idle'}`} />
            <span className="indicator-text">
              {is_running ? 'EXECUTANDO' : 'AGUARDANDO / FINALIZADO'}
            </span>
          </div>

          <div className="current-movie">
            <h3>Processando Agora:</h3>
            <p className="movie-name">{current_movie || "Nenhum"}</p>
          </div>

          <div className="progress-section">
            <div className="progress-info">
              <span>Progresso Total</span>
              <span>{percent}% ({progress?.current}/{progress?.total})</span>
            </div>
            <div className="progress-bar-bg">
              <motion.div 
                className="progress-bar-fill" 
                initial={{ width: 0 }}
                animate={{ width: `${percent}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </motion.div>

        {/* Logs Terminal */}
        <motion.div 
            className="logs-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
        >
          <div className="logs-header">
            <Terminal size={18} />
            <span>Logs do Sistema</span>
          </div>
          <div className="logs-content">
            {logs && logs.length > 0 ? (
              logs.slice().reverse().map((log, i) => (
                <div key={i} className="log-line">
                  {log}
                </div>
              ))
            ) : (
              <div className="log-line empty">Aguardando logs...</div>
            )}
          </div>
        </motion.div>
      </div>

      <style jsx>{`
        .status-page {
          min-height: 100vh;
          background: #0f0f0f;
          color: #fff;
          padding: 40px;
          font-family: 'Inter', sans-serif;
        }
        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 800px;
            margin: 0 auto 30px;
        }
        .status-header h1 {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 24px;
        }
        .back-link {
            color: #888;
            text-decoration: none;
            font-size: 14px;
            padding: 8px 16px;
            border: 1px solid #333;
            border-radius: 6px;
            transition: all 0.2s;
        }
        .back-link:hover {
            background: #222;
            color: #fff;
        }
        .status-container {
          max-width: 800px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .status-card, .logs-card {
          background: #1a1a1a;
          border: 1px solid #333;
          border-radius: 12px;
          padding: 24px;
        }
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 20px;
          font-weight: 600;
          letter-spacing: 1px;
          font-size: 0.9rem;
        }
        .indicator-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }
        .indicator-dot.running {
          background: #2ecc71;
          box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
          animation: pulse 1.5s infinite;
        }
        .indicator-dot.idle {
          background: #7f8c8d;
        }
        .current-movie h3 {
          font-size: 0.9rem;
          color: #888;
          margin-bottom: 5px;
          text-transform: uppercase;
        }
        .movie-name {
          font-size: 1.5rem;
          font-weight: 700;
          color: #fff;
        }
        .progress-section {
          margin-top: 30px;
        }
        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
          font-size: 0.9rem;
          color: #aaa;
        }
        .progress-bar-bg {
          width: 100%;
          height: 8px;
          background: #333;
          border-radius: 4px;
          overflow: hidden;
        }
        .progress-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #3498db, #8e44ad);
        }
        .logs-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 15px;
          color: #aaa;
          font-weight: 500;
        }
        .logs-content {
          background: #000;
          padding: 15px;
          border-radius: 8px;
          height: 300px;
          overflow-y: auto;
          font-family: 'Fira Code', monospace;
          font-size: 0.85rem;
          border: 1px solid #333;
        }
        .log-line {
          margin-bottom: 4px;
          color: #ccc;
          white-space: pre-wrap;
          word-break: break-all;
        }
        .log-line:first-child {
            color: #fff;
            font-weight: bold;
        }
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default ScraperStatus;
