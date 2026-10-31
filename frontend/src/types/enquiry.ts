export type EnquirySource = 'Email' | 'Phone' | 'Website';

export type EnquiryStatus =
  | 'New'
  | 'Contacted'
  | 'Registration Document Sent'
  | 'Registration Received'
  | 'Under Review'
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
  isReviewed?: boolean;
  reviewedBy?: string;
  reviewedAt?: string;
  createdAt: string;
}

export interface EmailAttachment {
  id: string;
  emailMessageId: string;
  originalFilename: string;
  fileSize: number;
  mimeType: string;
  createdAt: string;
  downloadUrl?: string;
}

export interface EmailMessage {
  id: string;
  enquiryId?: string;
  direction: 'incoming' | 'outgoing';
  senderName?: string;
  senderEmail: string;
  recipientEmail: string;
  subject: string;
  bodyText?: string;
  bodyHtml?: string;
  messageId?: string;
  threadId?: string;
  inReplyTo?: string;
  status: 'RECEIVED' | 'SENT' | 'FAILED' | 'PENDING' | 'UNCLASSIFIED' | 'ENQUIRY_CREATED' | 'ASSOCIATED' | 'IGNORED';
  errorMessage?: string;
  receivedAt?: string;
  sentAt?: string;
  createdAt: string;
  attachments?: EmailAttachment[];
}

export interface EmailStatus {
  imapConfigured: boolean;
  smtpConfigured: boolean;
  agencyEmail: string;
  imapHost: string;
  smtpHost?: string;
  lastSyncAt?: string;
  totalMessagesReceived: number;
  totalUnclassified: number;
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
  registrationReviewedAt?: string;
  clientId?: string;
  createdAt: string;
  updatedAt: string;
  notesHistory?: EnquiryNote[];
  documents?: DocumentSummary[];
  messages?: EmailMessage[];
}

export interface EnquiryListResponse {
  total: number;
  page: number;
  pageSize: number;
  items: Enquiry[];
}
