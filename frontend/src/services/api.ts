const API_BASE = 'http://localhost:8000/api/v1';

export const enquiryApi = {
  async list(params?: { search?: string; status?: string; source?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status && params.status !== 'All') searchParams.set('status', params.status);
    if (params?.source && params.source !== 'All') searchParams.set('source', params.source);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('page_size', String(params.pageSize));

    const res = await fetch(`${API_BASE}/enquiries?${searchParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch enquiries');
    return res.json();
  },

  async get(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch enquiry ${id}`);
    return res.json();
  },

  async create(data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/enquiries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to record enquiry');
    }
    return res.json();
  },

  async update(id: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/enquiries/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update enquiry');
    }
    return res.json();
  },

  async addNote(id: string, content: string, author: string = 'Agency Staff') {
    const res = await fetch(`${API_BASE}/enquiries/${id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, author }),
    });
    if (!res.ok) throw new Error('Failed to add note');
    return res.json();
  },

  async uploadDocument(id: string, file: File, documentType: 'sent_to_client' | 'completed_by_client') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('uploaded_by', 'Agency Staff');

    const res = await fetch(`${API_BASE}/enquiries/${id}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload document');
    }
    return res.json();
  },

  async sendDocument(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/send-document`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send registration document');
    }
    return res.json();
  },

  async markDocumentReceived(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/mark-document-received`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to mark document as received');
    }
    return res.json();
  },

  async registerClient(id: string, data?: { partner1Name?: string; partner2Name?: string; servicePackage?: string; additionalRequirements?: string; weddingTheme?: string }) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to register client');
    }
    return res.json();
  },

  getTemplateUrl(id: string) {
    return `${API_BASE}/enquiries/${id}/registration-template`;
  },

  getDownloadUrl(enquiryId: string, documentId: string) {
    return `${API_BASE}/enquiries/${enquiryId}/documents/${documentId}/download`;
  }
};

export const authApi = {
  async verifyToken(token: string) {
    const res = await fetch(`${API_BASE}/auth/verify-token?token=${encodeURIComponent(token)}`);
    return res.json();
  },

  async activate(payload: { token: string; password: string; confirmPassword: string }) {
    const res = await fetch(`${API_BASE}/auth/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Activation failed');
    }
    return res.json();
  },

  async login(payload: { email: string; password: string }) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  }
};
