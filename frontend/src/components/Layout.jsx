import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  FileText, 
  Plus, 
  Bell, 
  User,
  Menu,
  X
} from 'lucide-react'

function Layout() {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div>
      {/* Header */}
      <header className="header">
        {/* Logo */}
        <Link to="/" className="header-logo">
          <div className="header-logo-icon">
            <FileText size={20} />
          </div>
          <span className="header-logo-text">CVTeX</span>
        </Link>

        {/* Navigation Desktop */}
        <nav className="header-nav">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            Mes Candidatures
          </Link>
          <Link 
            to="/new" 
            className={location.pathname === '/new' ? 'active' : ''}
          >
            Nouvelle Candidature
          </Link>
        </nav>

        {/* Right side */}
        <div className="header-actions">
          <button className="btn-icon mobile-hide">
            <Bell size={20} />
          </button>
          <Link to="/new" className="btn-primary">
            <Plus size={16} />
            <span>Générer</span>
          </Link>
          <div className="avatar mobile-hide">
            <User size={20} />
          </div>
          {/* Mobile menu button */}
          <button 
            className="btn-icon mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {/* Mobile Navigation Overlay */}
      {mobileMenuOpen && (
        <nav className="mobile-nav">
          <Link 
            to="/" 
            className={`mobile-nav-item ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => setMobileMenuOpen(false)}
          >
            <FileText size={20} />
            Mes Candidatures
          </Link>
          <Link 
            to="/new" 
            className={`mobile-nav-item ${location.pathname === '/new' ? 'active' : ''}`}
            onClick={() => setMobileMenuOpen(false)}
          >
            <Plus size={20} />
            Nouvelle Candidature
          </Link>
        </nav>
      )}

      {/* Main content */}
      <main className="main-container">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
