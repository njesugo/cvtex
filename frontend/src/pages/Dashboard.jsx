import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search,
  Filter,
  LayoutGrid,
  Download,
  Plus,
  MapPin,
  ExternalLink,
  FileText,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Clock,
  XCircle,
  Sparkles,
  Loader2,
  Briefcase,
  TrendingUp,
  XOctagon,
  Trash2,
  Eye
} from 'lucide-react'
import api from '../api'

const statusConfig = {
  submitted: { label: 'Envoyée', color: 'green', icon: CheckCircle2 },
  under_review: { label: 'En cours', color: 'yellow', icon: Clock },
  shortlisted: { label: 'Présélectionné', color: 'blue', icon: Sparkles },
  rejected: { label: 'Refusée', color: 'red', icon: XCircle }
}

const sidebarFilters = [
  { key: 'all', label: 'Toutes les candidatures', icon: Briefcase },
  { key: 'submitted', label: 'Envoyées', icon: CheckCircle2 },
  { key: 'under_review', label: 'En cours', icon: Clock },
  { key: 'shortlisted', label: 'Présélectionnées', icon: TrendingUp },
  { key: 'rejected', label: 'Refusées', icon: XOctagon }
]

function Dashboard() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedRows, setSelectedRows] = useState([])
  const [showActions, setShowActions] = useState(null)
  const itemsPerPage = 10

  useEffect(() => {
    loadApplications()
  }, [])

  const loadApplications = async () => {
    try {
      const data = await api.getApplications()
      setApplications(data)
    } catch (err) {
      console.error('Failed to load applications:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredApplications = applications.filter(app => {
    const matchesFilter = activeFilter === 'all' || app.status === activeFilter
    const matchesSearch = 
      app.position.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.location.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const totalPages = Math.ceil(filteredApplications.length / itemsPerPage)
  const paginatedApplications = filteredApplications.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const getFilterCount = (key) => {
    if (key === 'all') return applications.length
    return applications.filter(a => a.status === key).length
  }

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  const toggleRowSelection = (id) => {
    setSelectedRows(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    )
  }

  const toggleAllRows = () => {
    if (selectedRows.length === paginatedApplications.length) {
      setSelectedRows([])
    } else {
      setSelectedRows(paginatedApplications.map(a => a.id))
    }
  }

  const handleDownload = (url) => {
    window.open(url, '_blank')
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric' 
    })
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Loader2 size={32} className="animate-spin" />
        <span>Chargement...</span>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <aside className="dashboard-sidebar">
        <div className="sidebar-section">
          <div className="sidebar-section-header">
            <span>Candidatures</span>
            <Link to="/new" className="sidebar-add-btn">+</Link>
          </div>
          <nav className="sidebar-filters">
            {sidebarFilters.map(filter => {
              const Icon = filter.icon
              const count = getFilterCount(filter.key)
              return (
                <button
                  key={filter.key}
                  onClick={() => {
                    setActiveFilter(filter.key)
                    setCurrentPage(1)
                  }}
                  className={`sidebar-filter-item ${activeFilter === filter.key ? 'active' : ''}`}
                >
                  <Icon size={16} />
                  <span className="filter-label">{filter.label}</span>
                  <span className="filter-count">{count}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Header */}
        <div className="dashboard-header">
          <h1 className="dashboard-title">Mes Candidatures</h1>
          <div className="dashboard-actions">
            <button className="action-btn secondary">
              <Download size={16} />
              Export
            </button>
            <Link to="/new" className="action-btn primary">
              <Plus size={16} />
              Nouvelle candidature
            </Link>
          </div>
        </div>

        {/* Toolbar */}
        <div className="dashboard-toolbar">
          <div className="search-container">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setCurrentPage(1)
              }}
              className="search-input"
            />
          </div>
          <div className="toolbar-actions">
            <button className="toolbar-btn">
              <Filter size={16} />
              Filtrer
            </button>
            <button className="toolbar-btn">
              <LayoutGrid size={16} />
              Vue
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="table-container">
          {applications.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <FileText size={40} />
              </div>
              <h2>Aucune candidature</h2>
              <p>Commencez par générer votre première candidature</p>
              <Link to="/new" className="action-btn primary">
                <Plus size={16} />
                Nouvelle candidature
              </Link>
            </div>
          ) : (
            <>
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="th-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedRows.length === paginatedApplications.length && paginatedApplications.length > 0}
                        onChange={toggleAllRows}
                        className="row-checkbox"
                      />
                    </th>
                    <th>Poste</th>
                    <th>Entreprise</th>
                    <th>Localisation</th>
                    <th>Documents</th>
                    <th>Statut</th>
                    <th>Match</th>
                    <th>Date</th>
                    <th className="th-actions"></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedApplications.map(app => {
                    const status = statusConfig[app.status]
                    return (
                      <tr 
                        key={app.id} 
                        className={selectedRows.includes(app.id) ? 'selected' : ''}
                      >
                        <td className="td-checkbox">
                          <input
                            type="checkbox"
                            checked={selectedRows.includes(app.id)}
                            onChange={() => toggleRowSelection(app.id)}
                            className="row-checkbox"
                          />
                        </td>
                        <td className="td-position">
                          <div className="position-cell">
                            <div className="company-avatar">
                              {getInitials(app.company)}
                            </div>
                            <div className="position-info">
                              <span className="position-title">{app.position}</span>
                              <span className="position-type">{app.type}</span>
                            </div>
                          </div>
                        </td>
                        <td className="td-company">
                          <span className="company-name">{app.company}</span>
                        </td>
                        <td className="td-location">
                          <div className="location-cell">
                            <MapPin size={14} />
                            <span>{app.location}</span>
                          </div>
                        </td>
                        <td className="td-documents">
                          <div className="documents-cell">
                            <button 
                              className="doc-btn cv"
                              onClick={() => handleDownload(app.cvPath)}
                              title="Télécharger le CV"
                            >
                              CV
                            </button>
                            <button 
                              className="doc-btn letter"
                              onClick={() => handleDownload(app.coverPath)}
                              title="Télécharger la lettre"
                            >
                              LM
                            </button>
                          </div>
                        </td>
                        <td className="td-status">
                          <span className={`status-badge ${status.color}`}>
                            {status.label}
                          </span>
                        </td>
                        <td className="td-match">
                          <div className="match-cell">
                            <div className="match-bar">
                              <div 
                                className="match-fill" 
                                style={{ width: `${app.matchScore}%` }}
                              />
                            </div>
                            <span className="match-value">{app.matchScore}%</span>
                          </div>
                        </td>
                        <td className="td-date">
                          <span className="date-text">{formatDate(app.appliedDate)}</span>
                        </td>
                        <td className="td-actions">
                          <div className="actions-cell">
                            <a 
                              href={app.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="action-icon"
                              title="Voir l'offre"
                            >
                              <ExternalLink size={16} />
                            </a>
                            <button 
                              className="action-icon"
                              onClick={() => setShowActions(showActions === app.id ? null : app.id)}
                            >
                              <MoreHorizontal size={16} />
                            </button>
                            {showActions === app.id && (
                              <div className="actions-dropdown">
                                <a 
                                  href={app.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="dropdown-item"
                                >
                                  <Eye size={14} />
                                  Voir l'offre
                                </a>
                                <button 
                                  className="dropdown-item"
                                  onClick={() => handleDownload(app.cvPath)}
                                >
                                  <FileText size={14} />
                                  Télécharger CV
                                </button>
                                <button 
                                  className="dropdown-item"
                                  onClick={() => handleDownload(app.coverPath)}
                                >
                                  <FileText size={14} />
                                  Télécharger LM
                                </button>
                                <button className="dropdown-item danger">
                                  <Trash2 size={14} />
                                  Supprimer
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="table-footer">
                <div className="pagination-info">
                  <span>Afficher</span>
                  <select 
                    className="page-size-select"
                    value={itemsPerPage}
                    disabled
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                  <span>
                    {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, filteredApplications.length)} sur {filteredApplications.length}
                  </span>
                </div>
                <div className="pagination-controls">
                  <button 
                    className="pagination-btn"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum
                    if (totalPages <= 5) {
                      pageNum = i + 1
                    } else if (currentPage <= 3) {
                      pageNum = i + 1
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i
                    } else {
                      pageNum = currentPage - 2 + i
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                  <button 
                    className="pagination-btn"
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Click outside handler for dropdown */}
      {showActions && (
        <div 
          className="dropdown-overlay"
          onClick={() => setShowActions(null)}
        />
      )}
    </div>
  )
}

export default Dashboard
