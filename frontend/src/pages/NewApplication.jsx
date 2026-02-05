import React, { useState } from 'react'
import { 
  Link2, 
  Loader2, 
  FileText, 
  Download,
  CheckCircle2,
  Sparkles,
  MapPin,
  Briefcase,
  ArrowRight,
  Eye,
  Building2,
  AlertCircle,
  Edit3,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

function NewApplication() {
  const navigate = useNavigate()
  const [jobUrl, setJobUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [step, setStep] = useState(1)
  const [jobData, setJobData] = useState(null)
  const [generatedFiles, setGeneratedFiles] = useState(null)
  const [previewData, setPreviewData] = useState(null)
  const [editedCV, setEditedCV] = useState(null)
  const [editedCover, setEditedCover] = useState(null)
  const [expandedSections, setExpandedSections] = useState({
    cv: true,
    skills: false,
    projects: false,
    cover: true
  })

  const handleGenerate = async () => {
    if (!jobUrl.trim()) return
    
    setIsLoading(true)
    setError(null)
    setStep(2)
    
    try {
      const data = await api.analyzeJob(jobUrl)
      setJobData(data)
      setStep(3)
    } catch (err) {
      setError(err.message)
      setStep(1)
    } finally {
      setIsLoading(false)
    }
  }

  const handlePreview = async () => {
    if (!jobData) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const preview = await api.previewDocuments(jobData.id)
      setPreviewData(preview)
      setEditedCV(preview.cv)
      setEditedCover(preview.coverLetter)
      setStep(4)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFinalize = async () => {
    if (!previewData) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const result = await api.finalizeDocuments(
        previewData.id,
        editedCV,
        editedCover
      )
      setGeneratedFiles({
        cv: result.cvPath,
        coverLetter: result.coverPath
      })
      setStep(5)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setJobUrl('')
    setStep(1)
    setJobData(null)
    setGeneratedFiles(null)
    setError(null)
  }

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  const handleDownload = async (path, filename) => {
    try {
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
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api'
      const baseUrl = API_BASE_URL.replace('/api', '')
      const url = path.startsWith('http') ? path : `${baseUrl}${path}`
      window.open(url, '_blank')
    }
  }

  return (
    <div className="new-application">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Nouvelle Candidature</h1>
        <p className="page-subtitle">
          Collez l'URL de l'offre d'emploi pour générer automatiquement votre CV et lettre de motivation
        </p>
      </div>

      {/* Progress steps */}
      <div className="progress-steps">
        {[
          { num: 1, label: 'URL' },
          { num: 2, label: 'Analyse' },
          { num: 3, label: 'Aperçu' },
          { num: 4, label: 'Édition' },
          { num: 5, label: 'Terminé' }
        ].map((s, idx) => (
          <React.Fragment key={s.num}>
            <div className="progress-step">
              <div className={`step-number ${step > s.num ? 'completed' : step === s.num ? 'current' : 'pending'}`}>
                {step > s.num ? <CheckCircle2 size={16} /> : s.num}
              </div>
              <span className={`step-label ${step >= s.num ? 'active' : 'pending'}`}>
                {s.label}
              </span>
            </div>
            {idx < 4 && (
              <div className={`step-line ${step > s.num ? 'completed' : 'pending'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: URL Input */}
      {step === 1 && (
        <div className="form-card">
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '12px',
              marginBottom: '20px',
              color: '#dc2626'
            }}>
              <AlertCircle size={20} />
              <span style={{ fontSize: '14px' }}>{error}</span>
            </div>
          )}
          <div className="form-group">
            <label className="form-label">URL de l'offre d'emploi</label>
            <div className="form-input-wrapper">
              <Link2 size={18} className="form-input-icon" />
              <input
                type="url"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://www.welcometothejungle.com/fr/companies/..."
                className="form-input"
              />
            </div>
            <p className="form-hint">
              Supporte Welcome to the Jungle, LinkedIn, Indeed, et autres sites d'emploi
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!jobUrl.trim()}
            className="btn-full primary"
          >
            <Sparkles size={18} />
            Analyser l'offre
          </button>

          {/* Recent URLs */}
          <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid #f3f4f6' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '16px' }}>
              Offres récentes
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { company: 'Stripe', position: 'Frontend Developer' },
                { company: 'Datadog', position: 'Full Stack Engineer' }
              ].map((recent, idx) => (
                <button
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    background: 'transparent',
                    border: 'none',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'background 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#f9fafb'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{
                    width: '40px',
                    height: '40px',
                    background: '#f3f4f6',
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#6b7280'
                  }}>
                    <Building2 size={18} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#111827' }}>
                      {recent.position}
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {recent.company}
                    </div>
                  </div>
                  <ArrowRight size={16} style={{ color: '#9ca3af' }} />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Loading */}
      {step === 2 && (
        <div className="form-card loading-card">
          <div className="loading-icon">
            <Loader2 size={32} className="animate-spin" />
          </div>
          <h2 className="loading-title">Analyse en cours...</h2>
          <p className="loading-subtitle">Extraction des informations de l'offre d'emploi</p>
          
          <div className="loading-tasks">
            {[
              { label: 'Extraction du contenu', done: true },
              { label: 'Détection de la langue', done: true },
              { label: 'Analyse des compétences', done: false }
            ].map((task, idx) => (
              <div key={idx} className={`loading-task ${task.done ? 'done' : 'pending'}`}>
                {task.done ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Loader2 size={16} className="animate-spin" />
                )}
                <span>{task.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Preview */}
      {step === 3 && jobData && (
        <div>
          <div className="preview-card">
            <div className="preview-header">
              <div className="preview-logo-container">
                {jobData.logoUrl && (
                  <img 
                    src={jobData.logoUrl} 
                    alt={jobData.company}
                    className="preview-logo"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      const placeholder = e.target.parentElement.querySelector('.detail-logo-placeholder')
                      if (placeholder) placeholder.style.display = 'flex'
                    }}
                  />
                )}
                <div 
                  className="detail-logo-placeholder"
                  style={{ display: jobData.logoUrl ? 'none' : 'flex' }}
                >
                  {getInitials(jobData.company)}
                </div>
              </div>
              <div className="preview-info">
                <h2 className="preview-title">{jobData.title}</h2>
                <p className="preview-company">{jobData.company}</p>
                <div className="preview-tags">
                  <span className="tag">
                    <MapPin size={12} />
                    {jobData.location}
                  </span>
                  <span className="tag">
                    <Briefcase size={12} />
                    {jobData.type}
                  </span>
                  <span className="tag">{jobData.salary}</span>
                </div>
              </div>
              <div className="preview-meta">
                <div className="match-score">
                  <Sparkles size={14} />
                  {jobData.matchScore}% Match
                </div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                  Langue: {jobData.language}
                </div>
              </div>
            </div>

            <div className="preview-summary">
              <h3 className="preview-summary-title">Résumé de l'offre</h3>
              <p className="preview-summary-text">{jobData.description}</p>
            </div>
          </div>

          <div className="docs-preview">
            <h3 className="docs-preview-title">Documents à générer</h3>
            <div className="docs-preview-grid">
              <div className="doc-preview-item cv">
                <div className="doc-preview-icon cv">
                  <FileText size={24} />
                </div>
                <div className="doc-preview-info">
                  <div className="name">CV Personnalisé</div>
                  <div className="desc">Adapté à l'offre</div>
                </div>
              </div>
              <div className="doc-preview-item letter">
                <div className="doc-preview-icon letter">
                  <FileText size={24} />
                </div>
                <div className="doc-preview-info">
                  <div className="name">Lettre de Motivation</div>
                  <div className="desc">Générée par IA</div>
                </div>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button onClick={resetForm} className="btn-full secondary">
              Annuler
            </button>
            <button
              onClick={handlePreview}
              disabled={isLoading}
              className="btn-full primary"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Préparation...
                </>
              ) : (
                <>
                  <Edit3 size={18} />
                  Personnaliser et générer
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Edit Documents */}
      {step === 4 && previewData && (
        <div className="form-card edit-card">
          <h2 className="edit-title">
            <Edit3 size={24} />
            Personnaliser vos documents
          </h2>
          <p className="edit-subtitle">
            Modifiez le contenu avant de générer les PDFs
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
                    placeholder="Ex: Développeur Full-Stack Senior"
                  />
                </div>
                <div className="edit-field">
                  <label>Résumé professionnel</label>
                  <textarea
                    value={editedCV.summary}
                    onChange={(e) => setEditedCV(prev => ({ ...prev, summary: e.target.value }))}
                    rows={4}
                    placeholder="Votre résumé professionnel adapté au poste..."
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
                      placeholder="Compétences séparées par des virgules..."
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
                        placeholder="Nom du projet..."
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
                        placeholder="Courte description du projet..."
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
                        placeholder="Python, React, Docker..."
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
                  <label>Accroche (premier paragraphe)</label>
                  <textarea
                    value={editedCover.accroche}
                    onChange={(e) => setEditedCover(prev => ({ ...prev, accroche: e.target.value }))}
                    rows={3}
                    placeholder="Phrase d'accroche captivante..."
                  />
                </div>
                <div className="edit-field">
                  <label>L'entreprise (pourquoi cette entreprise)</label>
                  <textarea
                    value={editedCover.entreprise}
                    onChange={(e) => setEditedCover(prev => ({ ...prev, entreprise: e.target.value }))}
                    rows={3}
                    placeholder="Ce qui vous attire dans cette entreprise..."
                  />
                </div>
                <div className="edit-field">
                  <label>Moi (vos compétences et expériences)</label>
                  <textarea
                    value={editedCover.moi}
                    onChange={(e) => setEditedCover(prev => ({ ...prev, moi: e.target.value }))}
                    rows={3}
                    placeholder="Vos atouts pour ce poste..."
                  />
                </div>
                <div className="edit-field">
                  <label>Nous (ce que vous apporterez)</label>
                  <textarea
                    value={editedCover.nous}
                    onChange={(e) => setEditedCover(prev => ({ ...prev, nous: e.target.value }))}
                    rows={3}
                    placeholder="Votre vision de la collaboration..."
                  />
                </div>
                <div className="edit-field">
                  <label>Conclusion</label>
                  <textarea
                    value={editedCover.conclusion}
                    onChange={(e) => setEditedCover(prev => ({ ...prev, conclusion: e.target.value }))}
                    rows={2}
                    placeholder="Formule de conclusion..."
                  />
                </div>
              </div>
            )}
          </div>

          <div className="form-actions">
            <button onClick={() => setStep(3)} className="btn-full secondary">
              Retour
            </button>
            <button
              onClick={handleFinalize}
              disabled={isLoading}
              className="btn-full primary"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Génération en cours...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Générer les PDFs
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Success */}
      {step === 5 && generatedFiles && (
        <div className="form-card success-card">
          <div className="success-icon">
            <CheckCircle2 size={40} />
          </div>
          <h2 className="success-title">Documents générés avec succès !</h2>
          <p className="success-subtitle">
            Votre CV et lettre de motivation sont prêts à être téléchargés
          </p>

          <div className="download-grid">
            <button 
              onClick={() => handleDownload(generatedFiles.cv, `CV_${jobData?.company || 'document'}.pdf`)}
              className="download-card"
            >
              <div className="download-card-icon cv">
                <FileText size={28} />
              </div>
              <div className="download-card-name">CV</div>
              <div className="download-card-action">
                <Download size={14} />
                Télécharger
              </div>
            </button>
            <button 
              onClick={() => handleDownload(generatedFiles.coverLetter, `LM_${jobData?.company || 'document'}.pdf`)}
              className="download-card"
            >
              <div className="download-card-icon letter">
                <FileText size={28} />
              </div>
              <div className="download-card-name">Lettre</div>
              <div className="download-card-action">
                <Download size={14} />
                Télécharger
              </div>
            </button>
          </div>

          <div className="success-actions">
            <button onClick={resetForm} className="btn-secondary">
              Nouvelle candidature
            </button>
            <Link to="/" className="btn-primary">
              <Eye size={16} />
              Voir mes candidatures
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default NewApplication