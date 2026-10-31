export interface WeddingFunction {
  name: string;
  date?: string;
  venue?: string;
  guest_count?: number;
  notes?: string;
}

export interface PaymentMilestone {
  id?: string;
  name: string;
  percentage: number;
  amount: number;
  due_date: string;
  description?: string;
}

export type AgreementStatus =
  | 'DRAFT'
  | 'PENDING_INTERNAL_APPROVAL'
  | 'APPROVED_TO_SEND'
  | 'SIGNING_PENDING'
  | 'SIGNED'
  | 'UNDER_VERIFICATION'
  | 'NEEDS_CORRECTION'
  | 'VERIFIED'
  | 'BOOKING_CONFIRMED'
  | 'EXPIRED'
  | 'CANCELLED'
  | 'REJECTED';

export type SigningStatus =
  | 'NOT_CREATED'
  | 'SENT'
  | 'PARTIALLY_SIGNED'
  | 'COMPLETED'
  | 'DECLINED'
  | 'EXPIRED'
  | 'CANCELLED'
  | 'FAILED';

export interface ServiceAgreement {
  id: string;
  agreement_number: string;
  client_id: string;
  status: AgreementStatus;
  signing_status: SigningStatus;
  wedding_date: string;
  wedding_location: string;
  venue?: string;
  guest_count: number;
  wedding_functions?: WeddingFunction[];
  service_package: string;
  included_services?: string[];
  excluded_services?: string[];
  deliverables?: string[];
  additional_terms?: string;

  package_price: number;
  tax_percentage: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  currency: string;

  current_version_number: number;
  is_internally_approved: boolean;
  approved_by?: string;
  approved_at?: string;

  is_verified: boolean;
  verified_by?: string;
  verified_at?: string;
  verification_notes?: string;

  created_by: string;
  created_at: string;
  updated_at: string;
  last_status_checked_at?: string;

  milestones: PaymentMilestone[];

  client_partner1_name?: string;
  client_partner2_name?: string;
  client_email?: string;
  client_phone?: string;
}

export interface AgreementMetrics {
  total_agreements: number;
  draft_agreements: number;
  pending_approval: number;
  signing_pending: number;
  signed_agreements: number;
  awaiting_verification: number;
  verified_agreements: number;
  confirmed_bookings: number;
}

export interface SignatureStatusResponse {
  agreement_id: string;
  agreement_number: string;
  version_number: number;
  signing_status: SigningStatus;
  agreement_status: AgreementStatus;
  provider: string;
  environment: 'sandbox' | 'production' | 'mock';
  provider_request_id?: string;
  provider_document_id?: string;
  leegality_document_id?: string;
  signing_url?: string;
  signer_name?: string;
  signer_email?: string;
  completed_at?: string;
  last_status_checked_at?: string;
  next_status_check_at?: string;
  polling_attempt_count?: number;
  last_polling_error?: string;
  has_signed_pdf?: boolean;
  has_audit_certificate?: boolean;
  raw_provider_status?: Record<string, any>;
}

export interface SendForSignatureResponse {
  success: boolean;
  message: string;
  agreement_id: string;
  agreement_number: string;
  version_number: number;
  provider: string;
  environment: 'sandbox' | 'production' | 'mock';
  provider_request_id?: string;
  provider_document_id?: string;
  leegality_document_id?: string;
  signing_url?: string;
  status: string;
  sent_at?: string;
}

