import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search,
  LayoutGrid,
  LayoutList,
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
  Eye,
  Download,
  Edit3,
  X,
  ChevronDown,
  ChevronUp,
  Mail,
  Calendar,
  ThumbsUp,
  MessageSquare
} from 'lucide-react'
import api from '../api'

const statusConfig = {
  submitted: { label: 'Envoyée', color: 'blue', icon: CheckCircle2 },
  ack_received: { label: 'Accusé reçu', color: 'cyan', icon: Mail },
  under_review: { label: 'En cours', color: 'yellow', icon: Clock },
  interview_scheduled: { label: 'Entretien prévu', color: 'purple', icon: Calendar },
  shortlisted: { label: 'Présélectionné', color: 'green', icon: ThumbsUp },
  offer: { label: 'Offre reçue', color: 'emerald', icon: Sparkles },
  rejected: { label: 'Refusée', color: 'red', icon: XCircle }
}

const sidebarFilters = [
  { key: 'all', label: 'Toutes les candidatures', icon: Briefcase },
  { key: 'submitted', label: 'Envoyées', icon: CheckCircle2 },
  { key: 'ack_received', label: 'Accusés reçus', icon: Mail },
  { key: 'under_review', label: 'En cours', icon: Clock },
  { key: 'interview_scheduled', label: 'Entretiens', icon: Calendar },
  { key: 'shortlisted', label: 'Présélectionnées', icon: TrendingUp },
  { key: 'offer', label: 'Offres', icon: Sparkles },
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
  const [viewMode, setViewMode] = useState('table') // 'table' or 'cards'
  const [editModal, setEditModal] = useState(null) // { id, data }
  const [editedCV, setEditedCV] = useState(null)
  const [editedCover, setEditedCover] = useState(null)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [expandedSections, setExpandedSections] = useState({ cv: true, skills: false, projects: false, cover: true })
  // Email analysis modal
  const [emailModal, setEmailModal] = useState(null) // { appId, company }
  const [emailContent, setEmailContent] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  // Status update modal
  const [statusModal, setStatusModal] = useState(null) // { appId, currentStatus }
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

  const handleDownload = async (path, filename) => {
    try {
      // Build full URL - path is like "/api/download/cv_xxx.pdf"
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api'
      const baseUrl = API_BASE_URL.replace('/api', '')
      const url = path.startsWith('http') ? path : `${baseUrl}${path}`
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Download failed')
      
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename || 'document.pdf'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error('Download failed:', err)
      // Fallback to opening in new tab
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api'
      const baseUrl = API_BASE_URL.replace('/api', '')
      const url = path.startsWith('http') ? path : `${baseUrl}${path}`
      window.open(url, '_blank')
    }
  }

  const handleEdit = async (id) => {
    try {
      setShowActions(null)
      const data = await api.getApplicationForEdit(id)
      setEditModal({ id, data })
      setEditedCV(data.cv)
      setEditedCover(data.coverLetter)
    } catch (err) {
      console.error('Edit load failed:', err)
      alert('Erreur lors du chargement des données')
    }
  }

  const handleRegenerate = async () => {
    if (!editModal || !editedCV || !editedCover) return
    
    setIsRegenerating(true)
    try {
      const result = await api.regenerateDocuments(editModal.id, editedCV, editedCover)
      
      // Update the application in the list with new paths
      setApplications(prev => prev.map(app => 
        app.id === editModal.id 
          ? { ...app, cvPath: result.cvPath, coverPath: result.coverPath }
          : app
      ))
      
      setEditModal(null)
      setEditedCV(null)
      setEditedCover(null)
      alert('Documents régénérés avec succès !')
    } catch (err) {
      console.error('Regenerate failed:', err)
      alert('Erreur lors de la régénération: ' + err.message)
    } finally {
      setIsRegenerating(false)
    }
  }

  const closeEditModal = () => {
    setEditModal(null)
    setEditedCV(null)
    setEditedCover(null)
  }

  // Email analysis functions
  const openEmailModal = (appId, company) => {
    setEmailModal({ appId, company })
    setEmailContent('')
    setAnalysisResult(null)
    setShowActions(null)
  }

  const closeEmailModal = () => {
    setEmailModal(null)
    setEmailContent('')
    setAnalysisResult(null)
  }

  const handleAnalyzeEmail = async () => {
    if (!emailContent.trim() || !emailModal) return
    
    setIsAnalyzing(true)
    try {
      const result = await api.analyzeEmail(emailModal.appId, emailContent)
      setAnalysisResult(result)
    } catch (err) {
      console.error('Analysis failed:', err)
      alert('Erreur lors de l\'analyse: ' + err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleApplyAnalysis = async () => {
    if (!analysisResult || !emailModal) return
    
    try {
      await api.updateApplicationFromEmail(emailModal.appId, {
        status: analysisResult.suggestedStatus,
        interviewDate: analysisResult.interviewDate,
        recruiterName: analysisResult.recruiterName,
        notes: analysisResult.notes
      })
      
      // Update local state
      setApplications(prev => prev.map(app => 
        app.id === emailModal.appId 
          ? { 
              ...app, 
              status: analysisResult.suggestedStatus,
              interviewDate: analysisResult.interviewDate,
              recruiterName: analysisResult.recruiterName
            }
          : app
      ))
      
      closeEmailModal()
      alert('Candidature mise à jour !')
    } catch (err) {
      console.error('Update failed:', err)
      alert('Erreur lors de la mise à jour: ' + err.message)
    }
  }

  // Manual status update
  const openStatusModal = (appId, currentStatus) => {
    setStatusModal({ appId, currentStatus })
    setShowActions(null)
  }

  const handleStatusChange = async (newStatus) => {
    if (!statusModal) return
    
    try {
      await api.updateStatus(statusModal.appId, newStatus)
      setApplications(prev => prev.map(app => 
        app.id === statusModal.appId ? { ...app, status: newStatus } : app
      ))
      setStatusModal(null)
    } catch (err) {
      console.error('Status update failed:', err)
      alert('Erreur lors de la mise à jour du statut')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette candidature ?')) {
      return
    }
    try {
      await api.deleteApplication(id)
      setApplications(prev => prev.filter(app => app.id !== id))
      setShowActions(null)
    } catch (err) {
      console.error('Delete failed:', err)
      alert('Erreur lors de la suppression')
    }
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
            <button 
              className={`toolbar-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
              title="Vue tableau"
            >
              <LayoutList size={16} />
            </button>
            <button 
              className={`toolbar-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
              title="Vue cartes"
            >
              <LayoutGrid size={16} />
            </button>
          </div>
        </div>

        {/* Content */}
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
          ) : viewMode === 'cards' ? (
            /* Cards View */
            <>
              <div className="cards-grid">
                {paginatedApplications.map(app => {
                  const status = statusConfig[app.status]
                  return (
                    <div key={app.id} className="application-card">
                      <div className="card-header">
                        <div className="card-company-info">
                          {app.logoUrl ? (
                            <img 
                              src={app.logoUrl} 
                              alt={app.company}
                              className="card-logo"
                              onError={(e) => {
                                e.target.style.display = 'none'
                                e.target.nextSibling.style.display = 'flex'
                              }}
                            />
                          ) : null}
                          <div 
                            className="card-avatar"
                            style={{ display: app.logoUrl ? 'none' : 'flex' }}
                          >
                            {getInitials(app.company)}
                          </div>
                          <div className="card-company-details">
                            <span className="card-company-name">{app.company}</span>
                            <span className="card-location">
                              <MapPin size={12} />
                              {app.location}
                            </span>
                          </div>
                        </div>
                        <span className={`status-badge ${status.color}`}>
                          {status.label}
                        </span>
                      </div>
                      <div className="card-body">
                        <h3 className="card-position">{app.position}</h3>
                        <span className="card-type">{app.type}</span>
                        <div className="card-match">
                          <div className="match-bar">
                            <div 
                              className="match-fill" 
                              style={{ width: `${app.matchScore}%` }}
                            />
                          </div>
                          <span className="match-value">{app.matchScore}% match</span>
                        </div>
                      </div>
                      <div className="card-footer">
                        <span className="card-date">{formatDate(app.appliedDate)}</span>
                        <div className="card-actions">
                          <button 
                            className="doc-btn cv"
                            onClick={() => handleDownload(app.cvPath, `CV_${app.company}_${app.position}.pdf`)}
                            title="Télécharger le CV"
                          >
                            <Download size={12} />
                            CV
                          </button>
                          <button 
                            className="doc-btn letter"
                            onClick={() => handleDownload(app.coverPath, `LM_${app.company}_${app.position}.pdf`)}
                            title="Télécharger la lettre"
                          >
                            <Download size={12} />
                            LM
                          </button>
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
                            onClick={() => handleEdit(app.id)}
                            title="Modifier les documents"
                          >
                            <Edit3 size={16} />
                          </button>
                          <button 
                            className="action-icon danger"
                            onClick={() => handleDelete(app.id)}
                            title="Supprimer"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              {/* Pagination for Cards */}
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
          ) : (
            /* Table View */
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
                            {app.logoUrl ? (
                              <img 
                                src={app.logoUrl} 
                                alt={app.company}
                                className="company-logo"
                                onError={(e) => {
                                  e.target.style.display = 'none'
                                  e.target.nextSibling.style.display = 'flex'
                                }}
                              />
                            ) : null}
                            <div 
                              className="company-avatar"
                              style={{ display: app.logoUrl ? 'none' : 'flex' }}
                            >
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
                              onClick={() => handleDownload(app.cvPath, `CV_${app.company}_${app.position}.pdf`)}
                              title="Télécharger le CV"
                            >
                              CV
                            </button>
                            <button 
                              className="doc-btn letter"
                              onClick={() => handleDownload(app.coverPath, `LM_${app.company}_${app.position}.pdf`)}
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
                                  onClick={() => handleDownload(app.cvPath, `CV_${app.company}_${app.position}.pdf`)}
                                >
                                  <FileText size={14} />
                                  Télécharger CV
                                </button>
                                <button 
                                  className="dropdown-item"
                                  onClick={() => handleDownload(app.coverPath, `LM_${app.company}_${app.position}.pdf`)}
                                >
                                  <FileText size={14} />
                                  Télécharger LM
                                </button>
                                <button 
                                  className="dropdown-item"
                                  onClick={() => handleEdit(app.id)}
                                >
                                  <Edit3 size={14} />
                                  Modifier les documents
                                </button>
                                <div className="dropdown-divider" />
                                <button 
                                  className="dropdown-item"
                                  onClick={() => openEmailModal(app.id, app.company)}
                                >
                                  <Mail size={14} />
                                  Analyser un email
                                </button>
                                <button 
                                  className="dropdown-item"
                                  onClick={() => openStatusModal(app.id, app.status)}
                                >
                                  <MessageSquare size={14} />
                                  Changer le statut
                                </button>
                                <div className="dropdown-divider" />
                                <button 
                                  className="dropdown-item danger"
                                  onClick={() => handleDelete(app.id)}
                                >
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

      {/* Edit Modal */}
      {editModal && editedCV && editedCover && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-content edit-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <Edit3 size={20} />
                Modifier les documents
              </h2>
              <button className="modal-close" onClick={closeEditModal}>
                <X size={20} />
              </button>
            </div>
            
            <div className="modal-body">
              <p className="edit-modal-subtitle">
                {editModal.data.jobInfo.company} - {editModal.data.jobInfo.title}
              </p>

              {/* CV Section */}
              <div className="edit-section">
                <button 
                  className="edit-section-header"
                  onClick={() => setExpandedSections(prev => ({ ...prev, cv: !prev.cv }))}
                >
                  <span>📄 CV - Résumé et titre</span>
                  {expandedSections.cv ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
                {expandedSections.cv && (
                  <div className="edit-section-content">
                    <div className="edit-field">
                      <label>Titre affiché sur le CV</label>
                      <input
                        type="text"
                        value={editedCV.display_title}
                        onChange={(e) => setEditedCV(prev => ({ ...prev, display_title: e.target.value }))}
                      />
                    </div>
                    <div className="edit-field">
                      <label>Résumé professionnel</label>
                      <textarea
                        value={editedCV.summary}
                        onChange={(e) => setEditedCV(prev => ({ ...prev, summary: e.target.value }))}
                        rows={4}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Skills Section */}
              <div className="edit-section">
                <button 
                  className="edit-section-header"
                  onClick={() => setExpandedSections(prev => ({ ...prev, skills: !prev.skills }))}
                >
                  <span>🛠️ Compétences</span>
                  {expandedSections.skills ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
                {expandedSections.skills && (
                  <div className="edit-section-content">
                    {editedCV.skills?.map((skill, idx) => (
                      <div key={idx} className="edit-field skill-field">
                        <label>{skill.label}</label>
                        <input
                          type="text"
                          value={skill.items.join(', ')}
                          onChange={(e) => {
                            const newSkills = [...editedCV.skills]
                            newSkills[idx] = { ...skill, items: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                            setEditedCV(prev => ({ ...prev, skills: newSkills }))
                          }}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Projects Section */}
              <div className="edit-section">
                <button 
                  className="edit-section-header"
                  onClick={() => setExpandedSections(prev => ({ ...prev, projects: !prev.projects }))}
                >
                  <span>🚀 Projets personnels</span>
                  {expandedSections.projects ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
                {expandedSections.projects && (
                  <div className="edit-section-content">
                    {editedCV.projects?.map((project, idx) => (
                      <div key={idx} className="project-edit-card">
                        <div className="edit-field">
                          <label>Nom du projet</label>
                          <input
                            type="text"
                            value={project.name}
                            onChange={(e) => {
                              const newProjects = [...editedCV.projects]
                              newProjects[idx] = { ...project, name: e.target.value }
                              setEditedCV(prev => ({ ...prev, projects: newProjects }))
                            }}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Description</label>
                          <textarea
                            value={project.description}
                            onChange={(e) => {
                              const newProjects = [...editedCV.projects]
                              newProjects[idx] = { ...project, description: e.target.value }
                              setEditedCV(prev => ({ ...prev, projects: newProjects }))
                            }}
                            rows={2}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Technologies</label>
                          <input
                            type="text"
                            value={project.technologies}
                            onChange={(e) => {
                              const newProjects = [...editedCV.projects]
                              newProjects[idx] = { ...project, technologies: e.target.value }
                              setEditedCV(prev => ({ ...prev, projects: newProjects }))
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Cover Letter Section */}
              <div className="edit-section">
                <button 
                  className="edit-section-header"
                  onClick={() => setExpandedSections(prev => ({ ...prev, cover: !prev.cover }))}
                >
                  <span>✉️ Lettre de motivation</span>
                  {expandedSections.cover ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
                {expandedSections.cover && (
                  <div className="edit-section-content">
                    <div className="edit-field">
                      <label>Accroche</label>
                      <textarea
                        value={editedCover.accroche}
                        onChange={(e) => setEditedCover(prev => ({ ...prev, accroche: e.target.value }))}
                        rows={3}
                      />
                    </div>
                    <div className="edit-field">
                      <label>L'entreprise</label>
                      <textarea
                        value={editedCover.entreprise}
                        onChange={(e) => setEditedCover(prev => ({ ...prev, entreprise: e.target.value }))}
                        rows={3}
                      />
                    </div>
                    <div className="edit-field">
                      <label>Moi</label>
                      <textarea
                        value={editedCover.moi}
                        onChange={(e) => setEditedCover(prev => ({ ...prev, moi: e.target.value }))}
                        rows={3}
                      />
                    </div>
                    <div className="edit-field">
                      <label>Nous</label>
                      <textarea
                        value={editedCover.nous}
                        onChange={(e) => setEditedCover(prev => ({ ...prev, nous: e.target.value }))}
                        rows={3}
                      />
                    </div>
                    <div className="edit-field">
                      <label>Conclusion</label>
                      <textarea
                        value={editedCover.conclusion}
                        onChange={(e) => setEditedCover(prev => ({ ...prev, conclusion: e.target.value }))}
                        rows={2}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeEditModal}>
                Annuler
              </button>
              <button 
                className="btn-primary"
                onClick={handleRegenerate}
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Régénération...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Régénérer les PDFs
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Analysis Modal */}
      {emailModal && (
        <div className="modal-overlay" onClick={closeEmailModal}>
          <div className="modal-content email-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <Mail size={20} />
                Analyser un email
              </h2>
              <button className="modal-close" onClick={closeEmailModal}>
                <X size={20} />
              </button>
            </div>
            
            <div className="modal-body">
              <p className="modal-subtitle">
                Collez le contenu de l'email reçu de <strong>{emailModal.company}</strong>
              </p>
              
              <div className="email-input-section">
                <textarea
                  className="email-textarea"
                  value={emailContent}
                  onChange={(e) => setEmailContent(e.target.value)}
                  placeholder="Collez ici le contenu de l'email du recruteur..."
                  rows={10}
                />
                
                <button 
                  className="btn-primary analyze-btn"
                  onClick={handleAnalyzeEmail}
                  disabled={isAnalyzing || !emailContent.trim()}
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Analyse en cours...
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      Analyser avec l'IA
                    </>
                  )}
                </button>
              </div>

              {analysisResult && (
                <div className="analysis-result">
                  <h3>Résultat de l'analyse</h3>
                  
                  <div className="analysis-item">
                    <span className="analysis-label">Type d'email :</span>
                    <span className="analysis-value">{analysisResult.emailType}</span>
                  </div>
                  
                  <div className="analysis-item">
                    <span className="analysis-label">Nouveau statut suggéré :</span>
                    <span className={`status-badge ${statusConfig[analysisResult.suggestedStatus]?.color || 'gray'}`}>
                      {statusConfig[analysisResult.suggestedStatus]?.label || analysisResult.suggestedStatus}
                    </span>
                  </div>
                  
                  {analysisResult.interviewDate && (
                    <div className="analysis-item">
                      <span className="analysis-label">Date d'entretien :</span>
                      <span className="analysis-value">{analysisResult.interviewDate}</span>
                    </div>
                  )}
                  
                  {analysisResult.recruiterName && (
                    <div className="analysis-item">
                      <span className="analysis-label">Recruteur :</span>
                      <span className="analysis-value">{analysisResult.recruiterName}</span>
                    </div>
                  )}
                  
                  {analysisResult.notes && (
                    <div className="analysis-item">
                      <span className="analysis-label">Notes :</span>
                      <span className="analysis-value">{analysisResult.notes}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeEmailModal}>
                Annuler
              </button>
              {analysisResult && (
                <button className="btn-primary" onClick={handleApplyAnalysis}>
                  <CheckCircle2 size={16} />
                  Appliquer les modifications
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Status Update Modal */}
      {statusModal && (
        <div className="modal-overlay" onClick={() => setStatusModal(null)}>
          <div className="modal-content status-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <MessageSquare size={20} />
                Changer le statut
              </h2>
              <button className="modal-close" onClick={() => setStatusModal(null)}>
                <X size={20} />
              </button>
            </div>
            
            <div className="modal-body">
              <div className="status-options">
                {Object.entries(statusConfig).map(([key, config]) => {
                  const Icon = config.icon
                  return (
                    <button
                      key={key}
                      className={`status-option ${statusModal.currentStatus === key ? 'current' : ''}`}
                      onClick={() => handleStatusChange(key)}
                    >
                      <Icon size={18} />
                      <span>{config.label}</span>
                      {statusModal.currentStatus === key && (
                        <span className="current-badge">Actuel</span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
