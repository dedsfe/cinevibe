import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage.jsx'
import ScraperStatus from './components/ScraperStatus.jsx'
import WatchPage from './components/WatchPage.jsx'
import SearchPage from './components/SearchPage.jsx'
import MoviesPage from './components/MoviesPage.jsx'
import AdminPage from './components/AdminPage.jsx'
import LinkVerifier from './components/LinkVerifier.jsx'
import MonitorPanel from './components/MonitorPanel.jsx'

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/movies" element={<MoviesPage />} />
          <Route path="/status" element={<ScraperStatus />} />
          <Route path="/watch/:id" element={<WatchPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/verify-links" element={<LinkVerifier />} />
          <Route path="/monitor" element={<MonitorPanel />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
