import React, { useState, useEffect } from 'react'
import { 
  MapPin, 
  DollarSign, 
  CheckCircle2, 
  Clock, 
  XCircle,
  Eye,
  FileText,
  Download,
  Search,
  Calendar,
  Sparkles,
  Circle,
  Loader2
} from 'lucide-react'
import api from '../api'

const statusConfig = {
  submitted: { label: 'Envoyée', icon: CheckCircle2 },
  under_review: { label: 'En cours', icon: Clock },
  shortlisted: { label: 'Présélectionné', icon: Sparkles },
  rejected: { label: 'Refusée', icon: XCircle }
}

const filters = [
  { key: 'all', label: 'Toutes' },
  { key: 'submitted', label: 'Envoyées' },
  { key: 'under_review', label: 'En cours' },
  { key: 'shortlisted', label: 'Présélectionnées' },
  { key: 'rejected', label: 'Refusées' }
]

function Dashboard() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')
  const [selectedApp, setSelectedApp] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadApplications()
  }, [])

  const loadApplications = async () => {
    try {
      const data = await api.getApplications()
      setApplications(data)
      if (data.length > 0) {
        setSelectedApp(data[0])
      }
    } catch (err) {
      console.error('Failed to load applications:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredApplications = applications.filter(app => {
    const matchesFilter = activeFilter === 'all' || app.status === activeFilter
    const matchesSearch = app.position.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         app.company.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const getFilterCount = (key) => {
    if (key === 'all') return applications.length
    return applications.filter(a => a.status === key).length
  }

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  const handleDownload = (path) => {
    const filename = path.split('/').pop()
    window.open(api.getDownloadUrl(filename), '_blank')
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Loader2 size={32} className="animate-spin" style={{ color: '#10b981' }} />
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-card">
          <h2 className="sidebar-title">Candidatures</h2>
          <nav className="sidebar-nav">
            {filters.map(filter => (
              <button
                key={filter.key}
                onClick={() => setActiveFilter(filter.key)}
                className={`sidebar-item ${activeFilter === filter.key ? 'active' : ''}`}
              >
                <span>{filter.label}</span>
                <span className="sidebar-count">{getFilterCount(filter.key)}</span>
              </button>
            ))}
          </nav>
        </div>
      </aside>

      {/* Content Area */}
      <div className="content-area">
        {/* Job List */}
        <div className="job-list-container">
          {/* Search */}
          <div className="search-box">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Applications */}
          <div className="job-list">
            {filteredApplications.map(app => {
              const StatusIcon = statusConfig[app.status].icon
              return (
                <div
                  key={app.id}
                  onClick={() => setSelectedApp(app)}
                  className={`job-card ${selectedApp?.id === app.id ? 'selected' : ''}`}
                >
                  <div className="job-card-header">
                    <div className="company-logo-placeholder">
                      {getInitials(app.company)}
                    </div>
                    <div className="job-card-info">
                      <h3 className="job-title">{app.position}</h3>
                      <p className="company-name">{app.company}</p>
                    </div>
                  </div>
                  
                  <div className="job-tags">
                    <span className="tag">
                      <MapPin size={12} />
                      {app.location}
                    </span>
                    <span className="tag">
                      <DollarSign size={12} />
                      {app.salary}
                    </span>
                    <span className="tag">{app.type}</span>
                  </div>

                  <div className="job-card-footer">
                    <span className="job-date">
                      <Calendar size={12} />
                      {app.appliedDate}
                    </span>
                    <span className={`status-badge status-${app.status}`}>
                      <StatusIcon size={12} />
                      {statusConfig[app.status].label}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Detail Panel */}
        {selectedApp && (
          <div className="detail-panel">
            <div className="detail-header">
              <div className="detail-header-left">
                <div className="detail-logo-placeholder">
                  {getInitials(selectedApp.company)}
                </div>
                <div>
                  <h1 className="detail-title">{selectedApp.position}</h1>
                  <p className="detail-company">{selectedApp.company}</p>
                </div>
              </div>
              <div className="detail-header-right">
                <a 
                  href={selectedApp.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn-secondary"
                >
                  <Eye size={14} />
                  Voir l'offre
                </a>
                <span className={`status-badge status-${selectedApp.status}`}>
                  {statusConfig[selectedApp.status].label}
                </span>
              </div>
            </div>

            {/* Tags */}
            <div className="detail-tags">
              <span className="tag">
                <MapPin size={12} />
                {selectedApp.location}
              </span>
              <span className="tag">
                <DollarSign size={12} />
                {selectedApp.salary}
              </span>
              <span className="tag">{selectedApp.type}</span>
              <span className="match-score">
                <Sparkles size={14} />
                {selectedApp.matchScore}% Match
              </span>
            </div>

            {/* Timeline */}
            <div className="timeline">
              <div className="timeline-step">
                <div className="timeline-icon completed">
                  <CheckCircle2 size={16} />
                </div>
                <div className="timeline-text">
                  <div className="label">Envoyée</div>
                  <div className="date">{selectedApp.appliedDate}</div>
                </div>
              </div>
              <div className={`timeline-line ${selectedApp.status !== 'submitted' ? 'completed' : 'pending'}`} />
              <div className="timeline-step">
                <div className={`timeline-icon ${selectedApp.status === 'under_review' || selectedApp.status === 'shortlisted' ? 'current' : 'pending'}`}>
                  <Clock size={16} />
                </div>
                <div className="timeline-text">
                  <div className="label">En cours</div>
                </div>
              </div>
              <div className="timeline-line pending" />
              <div className="timeline-step">
                <div className="timeline-icon pending">
                  <Circle size={16} />
                </div>
                <div className="timeline-text">
                  <div className="label">Décision</div>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="detail-section">
              <h3 className="detail-section-title">Description</h3>
              <p>{selectedApp.description}</p>
            </div>

            {/* Documents */}
            <div className="detail-section">
              <h3 className="detail-section-title">Documents générés</h3>
              <div className="documents-grid">
                <button 
                  className="document-card"
                  onClick={() => handleDownload(selectedApp.cvPath)}
                >
                  <div className="document-icon cv">
                    <FileText size={20} />
                  </div>
                  <div className="document-info">
                    <div className="document-name">CV</div>
                    <div className="document-action">Télécharger PDF</div>
                  </div>
                  <Download size={16} className="document-download" />
                </button>
                <button 
                  className="document-card"
                  onClick={() => handleDownload(selectedApp.coverPath)}
                >
                  <div className="document-icon letter">
                    <FileText size={20} />
                  </div>
                  <div className="document-info">
                    <div className="document-name">Lettre</div>
                    <div className="document-action">Télécharger PDF</div>
                  </div>
                  <Download size={16} className="document-download" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Empty state */}
        {applications.length === 0 && (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'white',
            borderRadius: '16px',
            padding: '48px',
            textAlign: 'center'
          }}>
            <div style={{
              width: '80px',
              height: '80px',
              background: '#dcfce7',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '24px'
            }}>
              <FileText size={32} style={{ color: '#10b981' }} />
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '8px' }}>
              Aucune candidature
            </h2>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px' }}>
              Commencez par générer votre première candidature
            </p>
            <a href="/new" className="btn-primary">
              <Sparkles size={16} />
              Nouvelle candidature
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard