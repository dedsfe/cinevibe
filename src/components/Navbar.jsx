import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Home, Film, Tv, Heart, Search } from 'lucide-react';
import '../styles/HomePage.css';

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
        <div className="logo" onClick={() => navigate('/home')}>Filfil</div>
        <ul className="nav-links">
          <li>
            <Link to="/home" className={isActive('/home') ? 'active' : ''}>
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
        </ul>
      </div>
      
      <div className="nav-right">
        <button className="nav-icon" onClick={onSearchClick}>
          <Search size={22} />
        </button>
      </div>
    </motion.nav>
  );
};

export default Navbar;
