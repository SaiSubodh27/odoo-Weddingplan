export type EnquirySource = 'Email' | 'Phone' | 'Website';

export type EnquiryStatus =
  | 'New'
  | 'Contacted'
  | 'Registration Link Sent'
  | 'Registration Submitted'
  | 'Registration Document Sent'
  | 'Registration Received'
  | 'Under Review'
  | 'Approved'
  | 'Corrections Requested'
  | 'Registered'
  | 'Closed';

export interface ClientRegistration {
  id: string;
  enquiryId: string;
  fullName: string;
  partnerName?: string;
  email: string;
  phone: string;
  address?: string;
  weddingDate?: string;
  weddingLocation?: string;
  expectedGuestCount?: number;
  estimatedBudget?: number;
  weddingEvents?: string;
  preferredTheme?: string;
  servicePackage: string;
  preferences?: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'CORRECTIONS_REQUESTED';
  reviewedBy?: string;
  reviewedAt?: string;
  reviewNotes?: string;
  correctionNotes?: string;
  submittedAt: string;
  createdAt: string;
  updatedAt: string;
}

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
  registrationToken?: string;
  registrationTokenExpiresAt?: string;
  registrationSentAt?: string;
  registrationReceivedAt?: string;
  registrationReviewedAt?: string;
  clientId?: string;
  createdAt: string;
  updatedAt: string;
  registration?: ClientRegistration;
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
