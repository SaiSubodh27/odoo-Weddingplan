export type CateringPlanStatus =
  | 'Draft'
  | 'Requirements Confirmed'
  | 'Quotation Requested'
  | 'Vendor Selected'
  | 'Menu Finalized'
  | 'Sent to Vendor'
  | 'Vendor Confirmed';

export type QuotationStatus =
  | 'Received'
  | 'Under Review'
  | 'Accepted'
  | 'Rejected'
  | 'Expired';

export type DietaryTag =
  | 'Vegetarian'
  | 'Non-Vegetarian'
  | 'Jain'
  | 'Vegan'
  | 'Contains Nuts'
  | 'Gluten-Free'
  | 'Halal';

export interface Vendor {
  id: string;
  name: string;
  contactPerson?: string | null;
  email?: string | null;
  phone: string;
  serviceCategory: string;
  city: string;
  address?: string | null;
  rating?: number | null;
  notes?: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CateringMenuItem {
  id: string;
  cateringPlanId: string;
  courseCategory: string;
  itemName: string;
  description?: string | null;
  dietaryTag: string;
  quantityNote?: string | null;
  displayOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface CateringQuotation {
  id: string;
  cateringPlanId: string;
  vendorId: string;
  quotationReference?: string | null;
  perPersonRate: number;
  totalGuestCount: number;
  foodSubtotal: number;
  equipmentCharges: number;
  gstRatePercent: number;
  gstAmount: number;
  totalAmount: number;
  status: QuotationStatus;
  validityDate?: string | null;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
  vendorName?: string | null;
  vendorPhone?: string | null;
  vendorContactPerson?: string | null;
  vendorCity?: string | null;
  vendorRating?: number | null;
}

export interface CateringCommunicationLog {
  id: string;
  cateringPlanId: string;
  vendorId?: string | null;
  communicationType: string;
  recipientPhone?: string | null;
  messageText?: string | null;
  pdfDownloadUrl?: string | null;
  status: string;
  initiatedBy: string;
  notes?: string | null;
  createdAt: string;
}

export interface CateringPlan {
  id: string;
  weddingProjectId: string;
  weddingFunctionId: string;
  guestCount: number;
  vegCount: number;
  nonVegCount: number;
  jainCount: number;
  dietaryNotes?: string | null;
  serviceStyle: string;
  serviceTimings?: string | null;
  location?: string | null;
  cuisinePreferences?: string | null;
  budget?: number | null;
  agreedCost?: number | null;
  status: CateringPlanStatus;
  selectedVendorId?: string | null;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
  selectedVendor?: Vendor | null;
  functionName?: string | null;
  functionDate?: string | null;
  functionVenue?: string | null;
  projectName?: string | null;
  menuItems: CateringMenuItem[];
  quotations: CateringQuotation[];
}

export interface PresetSummary {
  id: string;
  name: string;
  description: string;
  cuisineType: string;
  itemCount: number;
  courseBreakdown: Record<string, number>;
}

export interface PresetDetail extends PresetSummary {
  items: {
    courseCategory: string;
    itemName: string;
    description?: string;
    dietaryTag: string;
    quantityNote?: string;
  }[];
}

export interface CateringWhatsAppShareResponse {
  success: boolean;
  mode: string;
  shareUrl: string;
  recipientPhone: string;
  messageText: string;
  communicationId: string;
}
