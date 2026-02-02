import React, { useEffect, useState } from 'react';

// Lightweight monitor panel for local development. It queries the local monitor endpoints
// and renders a small health view without affecting scrapers.
const MonitorPanel = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchStatus = async () => {
      try {
        const h = await fetch('/monitor/health').then(r => r.json()).catch(() => null);
        if (mounted) setHealth(h);
      } catch (e) {
        // ignore
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchStatus();
    const t = setInterval(fetchStatus, 15000);
    return () => { mounted = false; clearInterval(t); };
  }, []);

  const ok = health && health.status === 'up';

  return (
    <section className="monitor-panel" style={{ padding: 20 }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span role="img" aria-label="monitor">🧭</span> Monitor de Operação
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        <div style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 12, padding: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>Status do Sistema</strong>
            <span style={{ padding: '2px 8px', borderRadius: 999, background: ok ? '#2ecc71' : '#e74c3c', color: '#fff' }}>
              {ok ? 'OK' : 'ALERTA'}
            </span>
          </div>
          <div style={{ marginTop: 8 }}>
            API: {health?.api?.reachable ? 'Reachable' : 'Indisponível'}
          </div>
          <div>Daemons: {health?.daemons ? Object.values(health.daemons).join(', ') : '—'}</div>
        </div>
        <div style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 12, padding: 16 }}>
          <strong>Saúde</strong>
          <div style={{ marginTop: 6 }}>{health?.status ? health.status.toUpperCase() : 'Avaliando...'}</div>
        </div>
        <div style={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 12, padding: 16 }}>
          <strong>Últimas adições</strong>
          <div style={{ color: '#ccc', fontFamily: 'monospace', fontSize: 12, marginTop: 6 }}>
            Dados disponíveis via API local
          </div>
        </div>
      </div>
    </section>
  );
};

export default MonitorPanel;
