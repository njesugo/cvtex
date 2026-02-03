import React from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  FileText, 
  Plus, 
  Bell, 
  User
} from 'lucide-react'

function Layout() {
  const location = useLocation()

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

        {/* Navigation */}
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
          <button className="btn-icon">
            <Bell size={20} />
          </button>
          <Link to="/new" className="btn-primary">
            <Plus size={16} />
            <span>Générer</span>
          </Link>
          <div className="avatar">
            <User size={20} />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="main-container">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
