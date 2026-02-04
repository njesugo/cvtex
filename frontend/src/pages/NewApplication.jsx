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
  AlertCircle
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

  const handleConfirm = async () => {
    if (!jobData) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const result = await api.generateDocuments(jobData.id)
      setGeneratedFiles({
        cv: result.cvPath,
        coverLetter: result.coverPath
      })
      setStep(4)
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
          { num: 4, label: 'Terminé' }
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
            {idx < 3 && (
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
              <div className="detail-logo-placeholder">
                {getInitials(jobData.company)}
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
              onClick={handleConfirm}
              disabled={isLoading}
              className="btn-full primary"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Génération...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Générer les documents
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Success */}
      {step === 4 && generatedFiles && (
        <div className="form-card success-card">
          <div className="success-icon">
            <CheckCircle2 size={40} />
          </div>
          <h2 className="success-title">Documents générés avec succès !</h2>
          <p className="success-subtitle">
            Votre CV et lettre de motivation sont prêts à être téléchargés
          </p>

          <div className="download-grid">
            <a 
              href={generatedFiles.cv} 
              target="_blank" 
              rel="noopener noreferrer"
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
            </a>
            <a 
              href={generatedFiles.coverLetter} 
              target="_blank"
              rel="noopener noreferrer" 
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
            </a>
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