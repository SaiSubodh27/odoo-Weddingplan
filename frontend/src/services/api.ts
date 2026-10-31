import { demoEnquiries, isDemoEnquiry } from '../data/demoEnquiries';

const API_BASE = 'http://localhost:8000/api/v1';

export const enquiryApi = {
  async list(params?: { search?: string; status?: string; source?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status && params.status !== 'All') searchParams.set('status', params.status);
    if (params?.source && params.source !== 'All') searchParams.set('source', params.source);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('page_size', String(params.pageSize));

    let liveItems: any[] = [];
    try {
      const res = await fetch(`${API_BASE}/enquiries?${searchParams.toString()}`);
      if (res.ok) {
        const data = await res.json();
        liveItems = data.items || [];
      }
    } catch {
      /* Graceful fallback */
    }

    const demo = demoEnquiries.filter(e =>
      (!params?.status || params.status === 'All' || e.status === params.status) &&
      (!params?.source || params.source === 'All' || e.enquirySource === params.source) &&
      (!params?.search || [e.clientName, e.email, e.phone, e.weddingLocation, e.id].join(' ').toLowerCase().includes(params.search.toLowerCase()))
    );

    const items = [...liveItems, ...demo];
    return { items, total: items.length, page: params?.page || 1, pageSize: items.length };
  },

  async get(id: string) {
    if (isDemoEnquiry(id)) {
      const demo = demoEnquiries.find(e => e.id === id);
      if (!demo) throw new Error('Demo enquiry not found');
      return demo;
    }
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

  async markDocumentReviewed(id: string, documentId?: string, reviewedBy: string = 'Agency Staff') {
    const url = new URL(`${API_BASE}/enquiries/${id}/mark-document-reviewed`);
    if (documentId) url.searchParams.set('document_id', documentId);
    url.searchParams.set('reviewed_by', reviewedBy);

    const res = await fetch(url.toString(), {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to mark document as reviewed');
    }
    return res.json();
  },

  async getMessages(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/messages`);
    if (!res.ok) throw new Error('Failed to fetch enquiry messages');
    return res.json();
  },

  async reply(id: string, payload: { body: string; subject?: string; attachRegistrationDocument?: boolean }) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send email reply');
    }
    return res.json();
  },

  async sendRegistrationLink(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/send-registration-link`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to dispatch online registration link');
    }
    return res.json();
  },

  async getRegistration(id: string) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/registration`);
    if (res.status === 404) return null;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch registration dossier');
    }
    return res.json();
  },

  async reviewRegistration(id: string, payload: { reviewedBy?: string; notes?: string }) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/registration/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to mark registration under review');
    }
    return res.json();
  },

  async requestCorrections(id: string, payload: { staffName?: string; correctionNotes: string }) {
    const res = await fetch(`${API_BASE}/enquiries/${id}/registration/request-corrections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to request registration corrections');
    }
    return res.json();
  },

  async approveRegistration(id: string, reviewedBy: string = 'Agency Staff') {
    const res = await fetch(`${API_BASE}/enquiries/${id}/registration/approve?reviewed_by=${encodeURIComponent(reviewedBy)}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to approve registration and dispatch activation email');
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

  getTemplateDownloadUrl(id: string) {
    return `${API_BASE}/enquiries/${id}/registration-template?download=true`;
  },

  getDownloadUrl(enquiryId: string, documentId: string) {
    return `${API_BASE}/enquiries/${enquiryId}/documents/${documentId}/download`;
  },

  getViewUrl(enquiryId: string, documentId: string) {
    return `${API_BASE}/enquiries/${enquiryId}/documents/${documentId}/download?inline=true`;
  }
};

export const emailApi = {
  async getStatus() {
    const res = await fetch(`${API_BASE}/emails/status`);
    if (!res.ok) throw new Error('Failed to fetch email status');
    return res.json();
  },

  async sync() {
    const res = await fetch(`${API_BASE}/emails/sync`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to sync emails');
    }
    return res.json();
  },

  async listInbox(params?: { statusFilter?: string; search?: string; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.statusFilter) searchParams.set('status_filter', params.statusFilter);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));

    const res = await fetch(`${API_BASE}/emails/inbox?${searchParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch inbox emails');
    return res.json();
  },

  async get(id: string) {
    const res = await fetch(`${API_BASE}/emails/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch email ${id}`);
    return res.json();
  },

  async convertToEnquiry(id: string, data?: { clientName?: string }) {
    const res = await fetch(`${API_BASE}/emails/${id}/convert-to-enquiry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to convert email to enquiry');
    }
    return res.json();
  },

  async associate(id: string, enquiryId: string) {
    const res = await fetch(`${API_BASE}/emails/${id}/associate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enquiryId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to associate email');
    }
    return res.json();
  },

  async ignore(id: string) {
    const res = await fetch(`${API_BASE}/emails/${id}/ignore`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to ignore email');
    }
    return res.json();
  },

  async simulate(formData: FormData) {
    const res = await fetch(`${API_BASE}/emails/simulate`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to simulate email');
    }
    return res.json();
  },

  getAttachmentUrl(emailId: string, attachmentId: string) {
    return `${API_BASE}/emails/${emailId}/attachments/${attachmentId}/download`;
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
  },

  async signup(payload: { fullName: string; email: string; phone?: string; password?: string; role?: string }) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  }
};

export const registrationApi = {
  async verifyToken(token: string) {
    const res = await fetch(`${API_BASE}/registrations/verify?token=${encodeURIComponent(token)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to verify registration token');
    }
    return res.json();
  },

  async submitRegistration(payload: any) {
    const res = await fetch(`${API_BASE}/registrations/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to submit registration form');
    }
    return res.json();
  }
};


export const projectApi = {
  async list(params?: { search?: string; status?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status && params.status !== 'All') searchParams.set('status', params.status);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('page_size', String(params.pageSize));

    const res = await fetch(`${API_BASE}/projects?${searchParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch wedding projects');
    return res.json();
  },

  async getEligibleBookings() {
    const res = await fetch(`${API_BASE}/projects/eligible-bookings`);
    if (!res.ok) throw new Error('Failed to fetch eligible bookings');
    return res.json();
  },

  async get(id: string) {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch project ${id}`);
    return res.json();
  },

  async create(data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create wedding project');
    }
    return res.json();
  },

  async update(id: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update wedding project');
    }
    return res.json();
  },

  async updateStatus(id: string, status: string, changedBy: string = 'Agency Staff', notes?: string) {
    const res = await fetch(`${API_BASE}/projects/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, changedBy, notes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update project status');
    }
    return res.json();
  },

  async addFunction(projectId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/functions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add wedding function');
    }
    return res.json();
  },

  async updateFunction(projectId: string, funcId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/functions/${funcId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update wedding function');
    }
    return res.json();
  },

  async deleteFunction(projectId: string, funcId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/functions/${funcId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete wedding function');
    }
    return res.json();
  },

  async addMilestone(projectId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/milestones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add project milestone');
    }
    return res.json();
  },

  async updateMilestone(projectId: string, msId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/milestones/${msId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update project milestone');
    }
    return res.json();
  },

  async deleteMilestone(projectId: string, msId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/milestones/${msId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete project milestone');
    }
    return res.json();
  },
};



export const vendorApi = {
  async list(params?: { category?: string; city?: string; search?: string; isActive?: boolean }) {
    const searchParams = new URLSearchParams();
    if (params?.category && params.category !== 'All') searchParams.set('category', params.category);
    if (params?.city && params.city !== 'All') searchParams.set('city', params.city);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.isActive !== undefined) searchParams.set('is_active', String(params.isActive));

    const res = await fetch(`${API_BASE}/vendors?${searchParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch vendors');
    return res.json();
  },

  async get(id: string) {
    const res = await fetch(`${API_BASE}/vendors/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch vendor ${id}`);
    return res.json();
  },

  async create(data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/vendors`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to register vendor');
    }
    return res.json();
  },

  async update(id: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/vendors/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update vendor');
    }
    return res.json();
  },

  async delete(id: string) {
    const res = await fetch(`${API_BASE}/vendors/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to deactivate vendor');
    }
    return res.json();
  },
};

export const cateringApi = {
  async getProjectCateringPlans(projectId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/catering`);
    if (!res.ok) throw new Error('Failed to fetch project catering plans');
    return res.json();
  },

  async getFunctionCateringPlan(projectId: string, functionId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/functions/${functionId}/catering`);
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error('Failed to fetch function catering plan');
    }
    return res.json();
  },

  async createPlan(projectId: string, functionId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/functions/${functionId}/catering`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create catering plan');
    }
    return res.json();
  },

  async updatePlan(cateringId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update catering requirements');
    }
    return res.json();
  },

  async updateStatus(cateringId: string, status: string, notes?: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, notes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update catering status');
    }
    return res.json();
  },

  async listMenuItems(cateringId: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/menu-items`);
    if (!res.ok) throw new Error('Failed to fetch menu items');
    return res.json();
  },

  async createMenuItem(cateringId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/menu-items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add dish to menu');
    }
    return res.json();
  },

  async updateMenuItem(cateringId: string, itemId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/menu-items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update menu dish');
    }
    return res.json();
  },

  async deleteMenuItem(cateringId: string, itemId: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/menu-items/${itemId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete dish');
    }
    return res.json();
  },

  async reorderMenuItems(cateringId: string, itemIds: string[]) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/menu-items/reorder`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itemIds),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to reorder menu items');
    }
    return res.json();
  },

  async listPresets() {
    const res = await fetch(`${API_BASE}/catering/presets`);
    if (!res.ok) throw new Error('Failed to fetch luxury menu presets');
    return res.json();
  },

  async getPreset(presetId: string) {
    const res = await fetch(`${API_BASE}/catering/presets/${presetId}`);
    if (!res.ok) throw new Error(`Failed to fetch preset ${presetId}`);
    return res.json();
  },

  async applyPreset(cateringId: string, presetId: string, mode: 'append' | 'replace' = 'append') {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/apply-preset/${presetId}?mode=${mode}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to apply menu preset');
    }
    return res.json();
  },

  async listQuotations(cateringId: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/quotations`);
    if (!res.ok) throw new Error('Failed to fetch catering quotations');
    return res.json();
  },

  async createQuotation(cateringId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/quotations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to record vendor quotation');
    }
    return res.json();
  },

  async updateQuotation(cateringId: string, quotationId: string, data: Record<string, any>) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/quotations/${quotationId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update quotation');
    }
    return res.json();
  },

  async selectWinningQuotation(cateringId: string, quotationId: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/quotations/${quotationId}/select`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to select winning caterer');
    }
    return res.json();
  },

  getQuotationPdfUrl(cateringId: string, quotationId: string) {
    return `${API_BASE}/catering/${cateringId}/quotations/${quotationId}/pdf`;
  },

  getCateringPlanPdfUrl(cateringId: string) {
    return `${API_BASE}/catering/${cateringId}/pdf`;
  },

  async shareWhatsApp(cateringId: string, payload: {
    quotationId?: string;
    vendorId?: string;
    recipientPhone?: string;
    customMessage?: string;
  }) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/share-whatsapp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quotationId: payload.quotationId,
        vendorId: payload.vendorId,
        recipientPhone: payload.recipientPhone,
        customMessage: payload.customMessage,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to generate WhatsApp share link');
    }
    return res.json();
  },

  async listCommunications(cateringId: string) {
    const res = await fetch(`${API_BASE}/catering/${cateringId}/communications`);
    if (!res.ok) throw new Error('Failed to fetch communications history');
    return res.json();
  },
};

export const agreementApi = {
  async getMyAgreement(clientId?: string) {
    const token = localStorage.getItem('the_royal_knot_token_v1') || '';
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const url = clientId ? `${API_BASE}/agreements/my-agreement?client_id=${clientId}` : `${API_BASE}/agreements/my-agreement`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Failed to fetch service agreement');
    return res.json();
  },

  async getAgreement(id: string) {
    const res = await fetch(`${API_BASE}/agreements/${id}`);
    if (!res.ok) throw new Error('Failed to fetch service agreement');
    return res.json();
  },

  async getClientAgreement(clientId: string) {
    const res = await fetch(`${API_BASE}/agreements/client/${clientId}`);
    if (!res.ok) throw new Error('Failed to fetch client agreement');
    return res.json();
  },

  async listAgreements(params?: { page?: number; pageSize?: number; status?: string }) {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.pageSize) q.set('page_size', String(params.pageSize));
    if (params?.status) q.set('status', params.status);
    const res = await fetch(`${API_BASE}/agreements?${q.toString()}`);
    if (!res.ok) throw new Error('Failed to list service agreements');
    return res.json();
  },

  async sendOtp(agreementId: string) {
    const res = await fetch(`${API_BASE}/agreements/${agreementId}/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to dispatch verification code');
    }
    return res.json();
  },

  async verifyOtp(agreementId: string, otp: string) {
    const res = await fetch(`${API_BASE}/agreements/${agreementId}/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ otp }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid or expired verification code');
    }
    return res.json();
  },

  async signAgreement(agreementId: string, payload: {
    otp?: string;
    signature_data: string;
    consent: boolean;
    signer_name?: string;
  }) {
    const res = await fetch(`${API_BASE}/agreements/${agreementId}/sign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to execute digital signature');
    }
    return res.json();
  },

  getPdfUrl(agreementId: string) {
    return `${API_BASE}/agreements/${agreementId}/pdf`;
  }
};
