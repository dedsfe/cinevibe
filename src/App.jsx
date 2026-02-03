import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './components/HomePage.jsx'
import WatchPage from './components/WatchPage.jsx'
import SearchPage from './components/SearchPage.jsx'
import MoviesPage from './components/MoviesPage.jsx'
import SeriesPage from './components/SeriesPage.jsx'
import MyListPage from './components/MyListPage.jsx'

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* Redirect root to movies page */}
          <Route path="/" element={<Navigate to="/movies" replace />} />
          <Route path="/movies" element={<MoviesPage />} />
          <Route path="/series" element={<SeriesPage />} />
          <Route path="/mylist" element={<MyListPage />} />
          <Route path="/watch/:id" element={<WatchPage />} />
          <Route path="/search" element={<SearchPage />} />
          {/* Redirect old login to movies */}
          <Route path="/login" element={<Navigate to="/movies" replace />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
