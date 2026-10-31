export type ProjectStatus = 
  | 'Planning' 
  | 'In Progress' 
  | 'On Hold' 
  | 'Completed' 
  | 'Cancelled';

export type FunctionStatus = 
  | 'Scheduled' 
  | 'In Progress' 
  | 'Completed' 
  | 'Cancelled';

export type MilestoneStatus = 
  | 'Pending' 
  | 'In Progress' 
  | 'Completed';

export interface WeddingFunction {
  id: string;
  projectId: string;
  functionName: string;
  functionDate: string;
  startTime?: string;
  endTime?: string;
  venue?: string;
  description?: string;
  status: FunctionStatus;
  estimatedCost: number | string;
  guestCountOverride?: number | null;
  eventNotes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectMilestone {
  id: string;
  projectId: string;
  milestoneName: string;
  assignedTo?: string | null;
  functionId?: string | null;
  category?: string;
  description?: string;
  dueDate: string;
  status: MilestoneStatus;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectStatusHistory {
  id: number;
  projectId: string;
  oldStatus?: string | null;
  newStatus: string;
  changedBy: string;
  notes?: string | null;
  changedAt: string;
}

export interface WeddingProject {
  id: string;
  projectCode: string;
  clientId: string;
  bookingId?: string | null;
  projectName: string;
  weddingDate: string;
  location: string;
  guestCount: number;
  estimatedBudget: number | string;
  packageTier: string;
  projectManagerName: string;
  status: ProjectStatus;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
  coupleName?: string;
  client?: {
    id: string;
    partner1Name: string;
    partner2Name: string;
    email: string;
    phone: string;
    status: string;
    weddingLocation: string;
    weddingDate: string;
    expectedGuestCount: number;
    estimatedBudget: number | string;
    servicePackage: string;
    weddingTheme?: string;
  };
  functions: WeddingFunction[];
  milestones: ProjectMilestone[];
  statusHistory: ProjectStatusHistory[];
}

export interface WeddingProjectListItem {
  id: string;
  projectCode: string;
  clientId: string;
  projectName: string;
  coupleName: string;
  weddingDate: string;
  location: string;
  guestCount: number;
  estimatedBudget: number | string;
  packageTier: string;
  projectManagerName: string;
  status: ProjectStatus;
  createdAt: string;
  functionsCount: number;
  completedMilestonesCount: number;
  totalMilestonesCount: number;
}

export interface EligibleBooking {
  clientId: string;
  partner1Name: string;
  partner2Name: string;
  coupleName: string;
  weddingDate: string;
  weddingLocation: string;
  expectedGuestCount: number;
  estimatedBudget: number | string;
  servicePackage: string;
  status: string;
  createdAt: string;
}

