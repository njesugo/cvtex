const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

export const api = {
  // Health check
  async health() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  // Get all applications
  async getApplications() {
    const response = await fetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw new Error('Failed to fetch applications');
    return response.json();
  },

  // Analyze a job URL
  async analyzeJob(url) {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze job');
    }
    return response.json();
  },

  // Generate documents
  async generateDocuments(id) {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate documents');
    }
    return response.json();
  },

  // Preview documents for editing
  async previewDocuments(id) {
    const response = await fetch(`${API_BASE_URL}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to preview documents');
    }
    return response.json();
  },

  // Finalize documents with edits
  async finalizeDocuments(id, cv, coverLetter) {
    const response = await fetch(`${API_BASE_URL}/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, cv, coverLetter })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to finalize documents');
    }
    return response.json();
  },

  // Download URL helper
  getDownloadUrl(path) {
    return `${API_BASE_URL}/download/${path}`;
  },

  // Delete application
  async deleteApplication(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete application');
    return response.json();
  },

  // Update application status
  async updateStatus(id, status) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}/status?status=${status}`, {
      method: 'PATCH'
    });
    if (!response.ok) throw new Error('Failed to update status');
    return response.json();
  },

  // Get application for editing
  async getApplicationForEdit(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}/edit`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to load application');
    }
    return response.json();
  },

  // Regenerate documents for existing application
  async regenerateDocuments(id, cv, coverLetter) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, cv, coverLetter })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to regenerate documents');
    }
    return response.json();
  },

  // Analyze email content with AI
  async analyzeEmail(appId, emailContent) {
    const response = await fetch(`${API_BASE_URL}/applications/${appId}/analyze-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: emailContent })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze email');
    }
    return response.json();
  },

  // Update application from email analysis
  async updateApplicationFromEmail(appId, data) {
    const response = await fetch(`${API_BASE_URL}/applications/${appId}/update-from-email`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update application');
    }
    return response.json();
  }
};

export default api;
