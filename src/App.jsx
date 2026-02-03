import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './components/HomePage.jsx'
import WatchPage from './components/WatchPage.jsx'
import SearchPage from './components/SearchPage.jsx'
import MoviesPage from './components/MoviesPage.jsx'
import SeriesPage from './components/SeriesPage.jsx'
import MyListPage from './components/MyListPage.jsx'
import LoginPage from './components/LoginPage.jsx'

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } />
            <Route path="/movies" element={
              <ProtectedRoute>
                <MoviesPage />
              </ProtectedRoute>
            } />
            <Route path="/series" element={
              <ProtectedRoute>
                <SeriesPage />
              </ProtectedRoute>
            } />
            <Route path="/mylist" element={
              <ProtectedRoute>
                <MyListPage />
              </ProtectedRoute>
            } />
            <Route path="/watch/:id" element={
              <ProtectedRoute>
                <WatchPage />
              </ProtectedRoute>
            } />
            <Route path="/search" element={
              <ProtectedRoute>
                <SearchPage />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  )
}

export default App
