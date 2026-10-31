export type RegistrationStatus = 
  | 'Enquiry' 
  | 'Registration Pending' 
  | 'Registered' 
  | 'Agreement Pending' 
  | 'Confirmed';

export type ServicePackage = 
  | 'Full-Service' 
  | 'Partial-Service' 
  | 'Day-of Coordination';

export type EnquirySource = 
  | 'Website' 
  | 'Email' 
  | 'Phone' 
  | 'Luxury Concierge' 
  | 'Referral';

export interface Client {
  id: string;
  // Couple details
  partner1Name: string;
  partner2Name: string;
  email: string;
  phone: string;
  
  // Wedding details
  weddingDate: string;
  weddingLocation: string;
  expectedGuestCount: number;
  estimatedBudget: string;
  weddingTheme: string;
  
  // Service details
  servicePackage: ServicePackage;
  additionalRequirements?: string;
  
  // Registration & Meta
  enquirySource: EnquirySource;
  notes?: string;
  status: RegistrationStatus;
  createdAt: string;
}

export interface UpcomingWeddingSchedule {
  id: string;
  coupleName: string;
  date: string;
  venue: string;
  city: 'Jaipur' | 'Udaipur';
  theme: string;
  servicePackage: string;
  daysRemaining: number;
  status: RegistrationStatus;
}

