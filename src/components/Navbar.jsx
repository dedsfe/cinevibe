import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Home, Film, Tv, Heart, Search, Bell, User, Shield, Activity } from 'lucide-react';
import '../styles/HomePage.css'; // Assuming styles are shared or I should eventually extract them

const Navbar = ({ onSearchClick }) => {
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path) => location.pathname === path;

  return (
    <motion.nav 
      className={`navbar ${scrolled ? 'scrolled' : ''}`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="nav-left">
        <div className="logo" onClick={() => navigate('/')}>CineVibe</div>
        <ul className="nav-links">
          <li>
            <Link to="/" className={isActive('/') ? 'active' : ''}>
              <Home size={18} /> Início
            </Link>
          </li>
          <li>
            <Link to="/movies" className={isActive('/movies') ? 'active' : ''}>
              <Film size={18} /> Filmes
            </Link>
          </li>
          <li>
            <Link to="/series" className={isActive('/series') ? 'active' : ''}>
              <Tv size={18} /> Séries
            </Link>
          </li>
          <li>
            <Link to="/mylist" className={isActive('/mylist') ? 'active' : ''}>
              <Heart size={18} /> Minha Lista
            </Link>
          </li>
          <li>
            <Link to="/admin" className={isActive('/admin') ? 'active' : ''} title="Painel de Administração">
              <Shield size={18} />
            </Link>
          </li>
          <li>
            <Link to="/monitor" className={isActive('/monitor') ? 'active' : ''}>
              <Activity size={18} /> Monitor
            </Link>
          </li>
        </ul>
      </div>
      
      <div className="nav-right">
        <button className="nav-icon" onClick={onSearchClick}>
          <Search size={22} />
        </button>
        <button className="nav-icon">
          <Bell size={22} />
        </button>
        <div className="profile">
          <User size={24} />
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
