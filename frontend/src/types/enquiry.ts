export type EnquirySource = 'Email' | 'Phone' | 'Website';

export type EnquiryStatus =
  | 'New'
  | 'Contacted'
  | 'Registration Document Sent'
  | 'Registration Received'
  | 'Registered'
  | 'Closed';

export interface EnquiryNote {
  id: number;
  enquiryId: string;
  author: string;
  content: string;
  createdAt: string;
}

export interface DocumentSummary {
  id: string;
  documentType: 'sent_to_client' | 'completed_by_client' | 'blank_template' | string;
  originalFilename: string;
  fileSize: number;
  mimeType: string;
  createdAt: string;
}

export interface Enquiry {
  id: string;
  clientName: string;
  email: string;
  phone: string;
  enquirySource: EnquirySource;
  weddingDate?: string;
  weddingLocation?: string;
  expectedGuestCount?: number;
  estimatedBudget?: string | number;
  requirements?: string;
  assignedStaff?: string;
  status: EnquiryStatus;
  internalNotes?: string;
  registrationSentAt?: string;
  registrationReceivedAt?: string;
  clientId?: string;
  createdAt: string;
  updatedAt: string;
  notesHistory?: EnquiryNote[];
  documents?: DocumentSummary[];
}

export interface EnquiryListResponse {
  total: number;
  page: number;
  pageSize: number;
  items: Enquiry[];
}
