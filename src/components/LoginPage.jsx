import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogIn, User, Lock, Eye, EyeOff, Tv } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, register, isAuthenticated } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already logged in
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (isLogin) {
      const result = await login(formData.username, formData.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error);
      }
    } else {
      const result = await register(formData.username, formData.password, formData.name);
      if (result.success) {
        // Auto login after register
        const loginResult = await login(formData.username, formData.password);
        if (loginResult.success) {
          navigate('/');
        }
      } else {
        setError(result.error);
      }
    }

    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="homepage" style={{ minHeight: '100vh' }}>
      <div className="content-container" style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        padding: '40px 20px'
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="login-container"
          style={{
            background: 'var(--bg-card)',
            borderRadius: '16px',
            padding: '40px',
            width: '100%',
            maxWidth: '420px',
            border: '1px solid var(--glass-border)'
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              gap: '12px',
              marginBottom: '24px'
            }}>
              <Tv size={40} color="#e50914" />
              <span style={{ fontSize: '1.75rem', fontWeight: 700 }}>Filfil</span>
            </div>
            <h1 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>
              {isLogin ? 'Bem-vindo de volta' : 'Criar conta'}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              {isLogin ? 'Entre para acessar sua lista' : 'Cadastre-se para começar'}
            </p>
          </div>

          {error && (
            <div style={{ 
              background: 'rgba(229, 9, 20, 0.1)', 
              color: '#e50914', 
              padding: '12px 16px', 
              borderRadius: '8px', 
              marginBottom: '20px',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {!isLogin && (
              <div style={{ position: 'relative' }}>
                <User size={18} style={{ 
                  position: 'absolute', 
                  left: '16px', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)'
                }} />
                <input
                  type="text"
                  name="name"
                  placeholder="Nome (opcional)"
                  value={formData.name}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '14px 16px 14px 48px',
                    borderRadius: '12px',
                    border: '1px solid var(--glass-border)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                />
              </div>
            )}

            <div style={{ position: 'relative' }}>
              <User size={18} style={{ 
                position: 'absolute', 
                left: '16px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }} />
              <input
                type="text"
                name="username"
                placeholder="Usuário"
                value={formData.username}
                onChange={handleChange}
                required
                style={{
                  width: '100%',
                  padding: '14px 16px 14px 48px',
                  borderRadius: '12px',
                  border: '1px solid var(--glass-border)',
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  fontSize: '1rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ 
                position: 'absolute', 
                left: '16px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }} />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                placeholder="Senha"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={4}
                style={{
                  width: '100%',
                  padding: '14px 48px 14px 48px',
                  borderRadius: '12px',
                  border: '1px solid var(--glass-border)',
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  fontSize: '1rem',
                  outline: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                background: 'var(--primary)',
                color: 'white',
                border: 'none',
                padding: '16px',
                borderRadius: '12px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '8px'
              }}
            >
              {loading ? (
                <div style={{ width: '20px', height: '20px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              ) : (
                <>
                  <LogIn size={18} />
                  {isLogin ? 'Entrar' : 'Cadastrar'}
                </>
              )}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '24px' }}>
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                cursor: 'pointer',
                fontSize: '0.95rem'
              }}
            >
              {isLogin ? 'Não tem conta? Cadastre-se' : 'Já tem conta? Entre'}
            </button>
          </div>

          {isLogin && (
            <div style={{ 
              marginTop: '24px', 
              padding: '16px', 
              background: 'rgba(255,255,255,0.05)', 
              borderRadius: '8px',
              fontSize: '0.85rem',
              color: 'var(--text-muted)'
            }}>
              <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}>Login padrão:</p>
              <p style={{ margin: 0 }}>Usuário: <code style={{ color: 'var(--text-primary)' }}>admin</code></p>
              <p style={{ margin: '4px 0 0 0' }}>Senha: <code style={{ color: 'var(--text-primary)' }}>admin123</code></p>
            </div>
          )}

          <style>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
