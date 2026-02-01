import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage.jsx'
import ScraperStatus from './components/ScraperStatus.jsx'
import WatchPage from './components/WatchPage.jsx'

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/status" element={<ScraperStatus />} />
          <Route path="/watch/:id" element={<WatchPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App