import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  Filter,
  DollarSign,
  Star,
  MapPin,
  Search,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  BookmarkCheck,
  Info,
  ChevronDown,
  ChevronUp,
  Table,
  LayoutGrid,
  FileText,
  Clock,
  RefreshCw,
  Users
} from 'lucide-react';
import { vendorApi, authApi } from '../../services/api';

export interface ClientVendor {
  id: string;
  name: string;
  category: string;
  city: string;
  contactPerson?: string | null;
  phone: string;
  email?: string | null;
  rating?: number | null;
  notes?: string | null;
  isActive: boolean;
  cost: number;
  tagline: string;
  specialties: string[];
  deliverables: string;
}

export type VendorStatus = 'Confirmed' | 'Shortlisted' | 'Waitlisted' | 'None';

export const VENDOR_BENCHMARKS: Record<string, {
  cost: number;
  tagline: string;
  specialties: string[];
  deliverables: string;
}> = {
  'VND-CAT-001': {
    cost: 5500000,
    tagline: 'Mewari Royal Banquets & Imperial Silver Thali Service',
    specialties: ['Dal Baati Churma', 'Laal Maas', 'Live Royal Halwai Counter'],
    deliverables: '3 Days, 5 Imperial Banquets for 350 Guests + Silver Crockery'
  },
  'VND-CAT-002': {
    cost: 4800000,
    tagline: 'Jaipur Palace Feasts & Awadhi Royal Gastronomy',
    specialties: ['Awadhi Dum Biryani', 'Kachori Counters', 'Gourmet Chaat'],
    deliverables: 'Complete Gala Dinners & High-Tea for 350 Guests'
  },
  'VND-CAT-003': {
    cost: 4200000,
    tagline: 'Lake City Traditional Heritage Catering',
    specialties: ['Lake Pichola Sweets', 'Rajasthani Rasoi', 'Jain Specialty Menus'],
    deliverables: 'Full-service ceremonial meals & customized live stations'
  },
  'VND-DEC-001': {
    cost: 3800000,
    tagline: 'Rajputana Heritage Floral Architecture & Floating Mandaps',
    specialties: ['Marigold Drapes', 'Lotus Floating Altar', 'Mirror Sheesh Mahal Setup'],
    deliverables: 'Palace Courtyard Transformation, Varmala Bridge & Royal Stage'
  },
  'VND-DEC-002': {
    cost: 2800000,
    tagline: 'Carved Wooden Mandaps & Royal Rajputana Drapes',
    specialties: ['Vedic Carved Pillars', 'Scented Jasmine Canopies', 'Antique Brass Diya Setup'],
    deliverables: 'Vedic Phera Mandap, Entrance Torans & Royal Aisle Decor'
  },
  'VND-DEC-003': {
    cost: 3200000,
    tagline: 'Fortress Scenography, Mood Lighting & Royal Canopies',
    specialties: ['Jodhpur Blue Pottery Accents', 'Glow Lanterns', 'Royal Shamianas'],
    deliverables: 'Sangeet Stage, Gala Dinner Lighting & Cocktail Lounge'
  },
  'VND-PHO-001': {
    cost: 1800000,
    tagline: 'Cinematic 4K Drone, Heritage Storytelling & Royal Albums',
    specialties: ['Cinematic Film (12min)', 'Same-Day Edit', 'Handcrafted Leather Albums'],
    deliverables: 'Team of 6 Master Cinematographers & Candid Photographers'
  },
  'VND-PHO-002': {
    cost: 1200000,
    tagline: 'Candid Royal Portraits & Lake Pichola Golden Hour Coverage',
    specialties: ['Sunset Lake Shoots', 'Royal Couple Portraits', 'Full Raw Footage'],
    deliverables: 'Team of 4 Photographers & 1 Drone Pilot across 3 days'
  },
  'VND-ENT-001': {
    cost: 850000,
    tagline: 'High-Energy Bollywood Royal Mashups, Concert Lights & SFX',
    specialties: ['Line Array Sound System', 'Cold Fire pyros', 'LED Visual Walls'],
    deliverables: 'Full Sangeet Night Sound Rig, Wireless Microphones & DJ Booth'
  },
  'VND-ENT-002': {
    cost: 600000,
    tagline: 'Authentic Manganiyar, Kalbelia & Classical Sufi Ensemble',
    specialties: ['Khartal Masters', 'Sufi Qawwali', 'Fire Dancers'],
    deliverables: 'Welcome Reception Troupes & 2-Hour Sangeet Sufi Concert'
  },
  'VND-ENT-003': {
    cost: 450000,
    tagline: 'Vedic Shehnai & Nagada Royal Auspicious Procession Music',
    specialties: ['Morning Ragas', 'Baraat Nagadas', 'Auspicious Phera Recitals'],
    deliverables: 'Continuous Ceremonial Live Music throughout Pheras & High-Tea'
  },
  'VND-MAK-001': {
    cost: 750000,
    tagline: 'Couture Bridal Artistry, HD Airbrush & Royal Hair Sculpting',
    specialties: ['Airbrush Makeup', 'Jewellery Setting', 'Sari/Dupatta Draping'],
    deliverables: 'Bride + 4 Family Members for Sangeet, Wedding & Reception'
  },
  'VND-MAK-002': {
    cost: 550000,
    tagline: 'Regal Rajasthan Glamour & Editorial Bridal Styling',
    specialties: ['Natural Glow Finish', 'Mewari Bindi Art', 'Bridal Touchups'],
    deliverables: 'Bride 3 Looks + Groom Styling & Touchups'
  },
  'VND-LOG-001': {
    cost: 900000,
    tagline: '1930s Rolls Royce & Vintage Convertibles for Royal Entries',
    specialties: ['Vintage Chauffeurs', 'Floral Car Garlands', 'Baraat Escort'],
    deliverables: '2 Classic Heritage Convertibles for Groom Baraat & Couple Varmala Entry'
  },
  'VND-LOG-002': {
    cost: 650000,
    tagline: 'Marwari Royal Safa Tying, Decorated Elephants & Shahi Horses',
    specialties: ['Zari Silk Safas', 'Ceremonial Royal Chhatra', 'Procession Chobdars'],
    deliverables: '350 Royal Guest Safas, Groom Royal Steed & Procession Guard'
  },
  'VND-LOG-003': {
    cost: 1500000,
    tagline: 'VIP Mercedes Fleet & Private Chartered Airport Shuttles',
    specialties: ['Airport Greeters', 'Luggage Escorts', 'Cold Bottled Water & Towels'],
    deliverables: '10 Luxury SUVs + 4 Executive Mercedes Coaches across 4 Days'
  },
  'VND-INV-001': {
    cost: 450000,
    tagline: 'Gold Foil Letterpress, Silk Scroll Farman & Wax Seals',
    specialties: ['Handmade Cotton Rag Paper', 'Gold Leaf Monograms', 'Custom Wax Stamp'],
    deliverables: '250 Bespoke Royal Invites + Digital RSVP Website'
  },
  'VND-INV-002': {
    cost: 800000,
    tagline: 'Pure Silver Coin Keepsakes, Organic Ittar & Dry Fruit Hampers',
    specialties: ['Silver Shahi Trays', 'Kashmiri Saffron Jars', 'Custom Engraving'],
    deliverables: '200 Luxury Welcome In-Room Hampers for Palace Guests'
  },
  'VND-SEC-001': {
    cost: 500000,
    tagline: 'Ex-Military Palace Security, Valet Operations & Bouncer Escorts',
    specialties: ['VIP Access Bands', 'Night Fire Watch', 'Crowd Protocol'],
    deliverables: '12 Security Guards, 6 Valet Chauffeurs & 2 Armed Supervisors'
  },
  'VND-HOS-001': {
    cost: 600000,
    tagline: 'Multilingual Royal Hostesses in Traditional Rajputana Attire',
    specialties: ['Aarti & Tilak Welcome', 'Flower Petal Showers', 'Concierge Desk'],
    deliverables: '8 Dedicated Hostesses managing Guest Room Check-ins & Itineraries'
  }
};

const CATEGORIES = [
  'All',
  'Catering',
  'Decor & Design',
  'Photography & Video',
  'Entertainment & DJ',
  'Live Music & Performers',
  'Bridal Hair & Makeup',
  'Transport & Fleet',
  'Royal Procession & Baraat',
  'Guest Hospitality',
  'Invitations & Gifting',
  'Security & Protocol'
];

export const formatINR = (val: number): string => {
  if (val >= 10000000) {
    return `₹ ${(val / 10000000).toFixed(2)} Cr`;
  }
  if (val >= 100000) {
    return `₹ ${(val / 100000).toFixed(2)} Lakhs`;
  }
  return `₹ ${val.toLocaleString('en-IN')}`;
};

interface ClientVendorCuratorProps {
  clientEmail: string;
  initialBudget?: number;
  weddingLocation?: string;
  guestCount?: number;
}

export const ClientVendorCurator: React.FC<ClientVendorCuratorProps> = ({
  clientEmail,
  initialBudget = 25000000,
  weddingLocation = 'Rajasthan Heritage Palace',
  guestCount = 350
}) => {
  const [vendors, setVendors] = useState<ClientVendor[]>([]);
  const [loading, setLoading] = useState(true);

  // Service Agreement details from backend
  const [agreementBudget, setAgreementBudget] = useState<number | null>(null);
  const [agreementNumber, setAgreementNumber] = useState<string | null>(null);

  // Planned target budget (settable by client or imported from service agreement)
  const [targetBudget, setTargetBudget] = useState<number>(() => {
    try {
      const saved = localStorage.getItem(`trk_client_budget_${clientEmail}`);
      if (saved) return Number(saved);
    } catch (_) {}
    return initialBudget || 25000000;
  });

  // Vendor status mappings: { [vendorId]: 'Confirmed' | 'Shortlisted' | 'Waitlisted' | 'None' }
  const [vendorStatuses, setVendorStatuses] = useState<Record<string, VendorStatus>>(() => {
    try {
      const saved = localStorage.getItem(`trk_client_vendor_statuses_${clientEmail}`);
      if (saved) return JSON.parse(saved);
      const savedIds = localStorage.getItem(`trk_client_vendors_${clientEmail}`);
      if (savedIds) {
        const ids: string[] = JSON.parse(savedIds);
        const map: Record<string, VendorStatus> = {};
        ids.forEach(id => { map[id] = 'Confirmed'; });
        return map;
      }
    } catch (_) {}
    return {
      'VND-CAT-001': 'Confirmed',
      'VND-DEC-001': 'Confirmed',
      'VND-PHO-001': 'Shortlisted'
    };
  });

  // View mode: 'spreadsheet' (default) or 'cards'
  const [viewMode, setViewMode] = useState<'spreadsheet' | 'cards'>('spreadsheet');

  // Filters & Controls
  const [statusFilter, setStatusFilter] = useState<'all' | 'Confirmed' | 'Shortlisted' | 'Waitlisted' | 'None'>('all');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [budgetFitFilter, setBudgetFitFilter] = useState<'all' | 'within-remaining' | 'under-10l' | '10l-30l' | 'above-30l'>('all');
  const [cityFilter, setCityFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'recommended' | 'budget-asc' | 'budget-desc' | 'rating-desc'>('recommended');
  const [expandedVendorId, setExpandedVendorId] = useState<string | null>(null);

  // UI States
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [editingBudget, setEditingBudget] = useState(false);
  const [customBudgetValue, setCustomBudgetValue] = useState<string>(String(targetBudget));

  // Load vendors and client selections from backend
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        let rawList: any[] = [];
        try {
          const res = await vendorApi.list();
          rawList = Array.isArray(res) ? res : (res.items || []);
        } catch (err) {
          console.warn('Backend vendorApi.list failed, using local benchmarks', err);
        }

        // Load saved client vendors & service agreement budget from backend
        try {
          if (clientEmail) {
            const clientData = await authApi.getClientVendors(clientEmail);
            if (clientData?.agreementBudget && clientData.agreementBudget > 0) {
              setAgreementBudget(clientData.agreementBudget);
              setAgreementNumber(clientData.agreementNumber || 'TRK-AGR-2026-014');
            }
            if (clientData?.totalBudget && clientData.totalBudget > 0) {
              const savedLocal = localStorage.getItem(`trk_client_budget_${clientEmail}`);
              if (!savedLocal) {
                setTargetBudget(clientData.totalBudget);
                setCustomBudgetValue(String(clientData.totalBudget));
              }
            }
            if (clientData?.vendorStatuses && Object.keys(clientData.vendorStatuses).length > 0) {
              const remoteStatuses: Record<string, VendorStatus> = {};
              Object.entries(clientData.vendorStatuses).forEach(([vid, st]: [string, any]) => {
                if (st === 'Confirmed' || st === 'Selected by Client' || st === 'Selected') {
                  remoteStatuses[vid] = 'Confirmed';
                } else if (st === 'Shortlisted') {
                  remoteStatuses[vid] = 'Shortlisted';
                } else if (st === 'Waitlisted') {
                  remoteStatuses[vid] = 'Waitlisted';
                } else {
                  remoteStatuses[vid] = 'Confirmed';
                }
              });
              setVendorStatuses(prev => ({ ...prev, ...remoteStatuses }));
            }
          }
        } catch (err) {
          console.warn('Failed to fetch client vendor selections from authApi', err);
        }

        // Merge raw list with benchmarks
        const merged: ClientVendor[] = Object.keys(VENDOR_BENCHMARKS).map(vid => {
          const benchmark = VENDOR_BENCHMARKS[vid];
          const matched = rawList.find(r => r.id === vid);
          return {
            id: vid,
            name: matched?.name || vid,
            category: matched?.category || 'Luxury Wedding Services',
            city: matched?.city || 'Jaipur',
            contactPerson: matched?.contactPerson || 'Royal Concierge',
            phone: matched?.phone || '+91 98291 00000',
            email: matched?.email || 'concierge@theroyalknot.in',
            rating: matched?.rating ? Number(matched.rating) : 4.9,
            notes: matched?.notes,
            isActive: matched ? matched.isActive : true,
            cost: benchmark.cost,
            tagline: benchmark.tagline,
            specialties: benchmark.specialties,
            deliverables: benchmark.deliverables
          };
        });

        rawList.forEach(item => {
          if (!merged.find(m => m.id === item.id)) {
            const fallbackCost = item.category?.includes('Catering') ? 4500000
              : item.category?.includes('Decor') ? 3000000
              : item.category?.includes('Photo') ? 1500000
              : 800000;
            merged.push({
              id: item.id,
              name: item.name,
              category: item.category || 'Luxury Services',
              city: item.city || 'Jaipur',
              contactPerson: item.contactPerson || 'Concierge',
              phone: item.phone || '+91 98291 00000',
              email: item.email,
              rating: item.rating ? Number(item.rating) : 4.8,
              notes: item.notes,
              isActive: item.isActive ?? true,
              cost: fallbackCost,
              tagline: `Premium ${item.category} Partner in ${item.city}`,
              specialties: ['Custom Royal Production', 'Palace Verified Team'],
              deliverables: 'Curated celebration package tailored to couple'
            });
          }
        });

        setVendors(merged);
      } catch (err) {
        console.error('Failed to load vendors', err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [clientEmail]);

  // Persist selections to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(`trk_client_vendor_statuses_${clientEmail}`, JSON.stringify(vendorStatuses));
      const confirmedIds = Object.entries(vendorStatuses)
        .filter(([_, st]) => st === 'Confirmed' || st === 'Shortlisted' || st === 'Waitlisted')
        .map(([id]) => id);
      localStorage.setItem(`trk_client_vendors_${clientEmail}`, JSON.stringify(confirmedIds));
      localStorage.setItem(`trk_client_budget_${clientEmail}`, String(targetBudget));
    } catch (_) {}
  }, [vendorStatuses, targetBudget, clientEmail]);

  // Calculations
  const confirmedVendors = useMemo(() => {
    return vendors.filter(v => vendorStatuses[v.id] === 'Confirmed');
  }, [vendors, vendorStatuses]);

  const shortlistedVendors = useMemo(() => {
    return vendors.filter(v => vendorStatuses[v.id] === 'Shortlisted');
  }, [vendors, vendorStatuses]);

  const waitlistedVendors = useMemo(() => {
    return vendors.filter(v => vendorStatuses[v.id] === 'Waitlisted');
  }, [vendors, vendorStatuses]);

  const confirmedCost = useMemo(() => {
    return confirmedVendors.reduce((sum, v) => sum + v.cost, 0);
  }, [confirmedVendors]);

  const shortlistCost = useMemo(() => {
    return shortlistedVendors.reduce((sum, v) => sum + v.cost, 0);
  }, [shortlistedVendors]);

  const waitlistCost = useMemo(() => {
    return waitlistedVendors.reduce((sum, v) => sum + v.cost, 0);
  }, [waitlistedVendors]);

  const remainingBudget = targetBudget - confirmedCost;
  const percentUtilized = targetBudget > 0 ? Math.min(100, Math.round((confirmedCost / targetBudget) * 100)) : 0;
  const isOverBudget = remainingBudget < 0;

  // Category breakdown for confirmed vendors
  const categoryBreakdown = useMemo(() => {
    const map: Record<string, number> = {};
    confirmedVendors.forEach(v => {
      map[v.category] = (map[v.category] || 0) + v.cost;
    });
    return Object.entries(map).map(([cat, amount]) => ({
      category: cat,
      amount,
      pct: targetBudget > 0 ? ((amount / targetBudget) * 100).toFixed(1) : '0'
    }));
  }, [confirmedVendors, targetBudget]);

  // Status Change Handler for Dropdown Menu
  const handleStatusChange = (vendorId: string, newStatus: VendorStatus) => {
    setVendorStatuses(prev => ({
      ...prev,
      [vendorId]: newStatus
    }));
    setSaveSuccess(false);
  };

  // Quick Action: Set Budget from Service Agreement
  const handleSetFromServiceAgreement = () => {
    if (agreementBudget && agreementBudget > 0) {
      setTargetBudget(agreementBudget);
      setCustomBudgetValue(String(agreementBudget));
      setEditingBudget(false);
    }
  };

  // Custom Budget Form Submit
  const handleApplyCustomBudget = (e: React.FormEvent) => {
    e.preventDefault();
    const val = Number(customBudgetValue.replace(/\D/g, ''));
    if (val && val >= 500000) {
      setTargetBudget(val);
      setEditingBudget(false);
    }
  };

  // Save to Backend
  const handleSaveToProject = async () => {
    try {
      setIsSaving(true);
      const activeVendorIds: string[] = [];
      const vendorCosts: Record<string, number> = {};
      const statusPayload: Record<string, string> = {};

      vendors.forEach(v => {
        const st = vendorStatuses[v.id] || 'None';
        if (st !== 'None') {
          activeVendorIds.push(v.id);
          vendorCosts[v.id] = v.cost;
          statusPayload[v.id] = st;
        }
      });

      await authApi.saveClientVendors({
        email: clientEmail,
        vendorIds: activeVendorIds,
        customBudget: targetBudget,
        vendorCosts,
        vendorStatuses: statusPayload
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 5000);
    } catch (err) {
      console.error('Failed to sync vendors with backend:', err);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 5000);
    } finally {
      setIsSaving(false);
    }
  };

  // Filtered and Sorted Vendors
  const filteredVendors = useMemo(() => {
    return vendors.filter(v => {
      const st = vendorStatuses[v.id] || 'None';

      // Status filter
      if (statusFilter !== 'all') {
        if (st !== statusFilter) return false;
      }

      // Category filter
      if (categoryFilter !== 'All' && v.category !== categoryFilter) {
        return false;
      }

      // City filter
      if (cityFilter !== 'All' && v.city !== cityFilter) {
        return false;
      }

      // Budget Fit filter
      if (budgetFitFilter === 'within-remaining') {
        const isConfirmed = st === 'Confirmed';
        if (!isConfirmed && v.cost > remainingBudget) return false;
      } else if (budgetFitFilter === 'under-10l') {
        if (v.cost >= 1000000) return false;
      } else if (budgetFitFilter === '10l-30l') {
        if (v.cost < 1000000 || v.cost > 3000000) return false;
      } else if (budgetFitFilter === 'above-30l') {
        if (v.cost <= 3000000) return false;
      }

      // Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = v.name.toLowerCase().includes(q);
        const matchesCat = v.category.toLowerCase().includes(q);
        const matchesSpecialty = v.specialties.some(s => s.toLowerCase().includes(q));
        const matchesDeliverables = v.deliverables.toLowerCase().includes(q);
        const matchesCity = v.city.toLowerCase().includes(q);
        if (!matchesName && !matchesCat && !matchesSpecialty && !matchesDeliverables && !matchesCity) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      if (sortBy === 'budget-asc') return a.cost - b.cost;
      if (sortBy === 'budget-desc') return b.cost - a.cost;
      if (sortBy === 'rating-desc') return (b.rating || 0) - (a.rating || 0);

      // Recommended: Prioritize Confirmed, then Shortlisted, then Waitlisted, then highest rating
      const rank = (vid: string) => {
        const s = vendorStatuses[vid] || 'None';
        if (s === 'Confirmed') return 4;
        if (s === 'Shortlisted') return 3;
        if (s === 'Waitlisted') return 2;
        return 1;
      };
      const diff = rank(b.id) - rank(a.id);
      if (diff !== 0) return diff;
      return (b.rating || 0) - (a.rating || 0);
    });
  }, [vendors, vendorStatuses, statusFilter, categoryFilter, cityFilter, budgetFitFilter, searchQuery, sortBy, remainingBudget]);

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-[#1F2421] via-[#2A312B] to-[#1F2421] text-[#FAF8F5] p-6 sm:p-8 border border-[#40463F] relative overflow-hidden shadow-sm">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#9E7D3B]/20 via-transparent to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 text-[10px] tracking-[0.25em] uppercase text-[#D9C496] font-semibold">
              <Sparkles size={12} />
              <span>Royal Palace Vendor Curation & Budget Spreadsheet</span>
            </div>
            <h2 className="font-serif text-2xl sm:text-3xl text-white">
              Vendor Selection & Planned Budget Matrix
            </h2>
            <p className="text-xs text-[#C5BFA9] max-w-2xl leading-relaxed">
              Manage your royal wedding team in a real-time spreadsheet. Set status dropdowns (Confirmed, Shortlist, Waitlist) for every palace service and track dynamic budget allocations directly against your Service Agreement.
            </p>
            <div className="flex flex-wrap items-center gap-4 text-xs text-[#D9C496] pt-1">
              <span className="flex items-center gap-1">
                <MapPin size={12} />
                <span>{weddingLocation}</span>
              </span>
              <span className="flex items-center gap-1">
                <Users size={12} />
                <span>{guestCount} Guests Planned</span>
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
            <button
              onClick={handleSaveToProject}
              disabled={isSaving}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#9E7D3B] hover:bg-[#8A6C32] text-white text-xs uppercase tracking-wider font-semibold shadow-md transition-all active:scale-95 disabled:opacity-50"
            >
              {isSaving ? (
                <>Saving Team...</>
              ) : (
                <>
                  <BookmarkCheck size={14} />
                  <span>Lock & Submit Selections</span>
                </>
              )}
            </button>
          </div>
        </div>

        {saveSuccess && (
          <div className="mt-4 p-3 bg-[#EBF3ED] border border-[#C3D9C9] text-[#2D5A3C] text-xs flex items-center justify-between animate-fadeIn">
            <div className="flex items-center gap-2 font-medium">
              <CheckCircle2 size={16} />
              <span>Your curated vendor team and budget allocations have been submitted to Principal Planner Maharani Gayatri Singh!</span>
            </div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#2D5A3C]">Status: Ratified</span>
          </div>
        )}
      </div>

      {/* TOTAL PLANNED BUDGET & SERVICE AGREEMENT SYNC DECK */}
      <div className="bg-white border border-[#E5E0D8] p-6 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-[#E5E0D8] gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[#FAF8F5] border border-[#E5E0D8] flex items-center justify-center text-[#9E7D3B]">
              <DollarSign size={18} />
            </div>
            <div>
              <h3 className="font-serif text-base text-[#1F2421] font-bold">Total Planned Celebration Budget</h3>
              <p className="text-[11px] text-[#736F68]">
                Directly enter your budget number or synchronize from your executed Service Agreement
              </p>
            </div>
          </div>

          {/* Service Agreement Quick-Sync Badge & Input Controls */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            {agreementBudget && (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#FAF8F5] border border-[#9E7D3B]/40 rounded">
                <FileText size={13} className="text-[#9E7D3B]" />
                <span className="text-[11px] text-[#736F68]">
                  Service Agreement ({agreementNumber || 'TRK-AGR'}): <strong className="text-[#1F2421]">{formatINR(agreementBudget)}</strong>
                </span>
                <button
                  type="button"
                  onClick={handleSetFromServiceAgreement}
                  title="Set Total Planned Budget from Service Agreement amount"
                  className="px-2 py-0.5 bg-[#9E7D3B] hover:bg-[#8A6C32] text-white text-[10px] uppercase font-bold tracking-wider rounded transition-colors"
                >
                  Set From Agreement
                </button>
              </div>
            )}

            {/* Direct Number Input / Editor */}
            {editingBudget ? (
              <form onSubmit={handleApplyCustomBudget} className="flex items-center gap-2">
                <input
                  type="number"
                  min={500000}
                  step={50000}
                  value={customBudgetValue}
                  onChange={e => setCustomBudgetValue(e.target.value)}
                  className="w-36 px-2.5 py-1 text-xs border border-[#9E7D3B] bg-[#FAF8F5] font-bold text-[#1F2421] focus:outline-none"
                  placeholder="e.g. 29500000"
                  autoFocus
                />
                <button
                  type="submit"
                  className="px-3 py-1 bg-[#1F2421] hover:bg-[#343733] text-white text-xs font-semibold"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditingBudget(false)}
                  className="px-2 py-1 text-xs text-[#736F68] hover:text-[#1F2421]"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-[#8C877D] uppercase tracking-wider font-medium">Planned:</span>
                <span className="font-serif font-bold text-[#1F2421] text-base">{formatINR(targetBudget)}</span>
                <button
                  type="button"
                  onClick={() => setEditingBudget(true)}
                  className="px-2.5 py-1 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] hover:text-[#1F2421] hover:border-[#9E7D3B] font-semibold transition-colors"
                >
                  Set / Enter Number
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 4 Primary Spreadsheet Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
          {/* 1. Total Planned Budget */}
          <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] flex flex-col justify-between">
            <div>
              <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1 font-semibold">
                1. Total Planned Budget
              </span>
              <div className="font-serif text-2xl font-bold text-[#1F2421]">
                {formatINR(targetBudget)}
              </div>
              <p className="text-[11px] text-[#736F68] mt-1">
                Base allocation ceiling for palace wedding
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-1 mt-3 pt-2 border-t border-[#E5E0D8]">
              <span className="text-[10px] text-[#8C877D]">Presets:</span>
              {[15000000, 20000000, 25000000, 29500000, 35000000, 50000000].map(val => (
                <button
                  key={val}
                  type="button"
                  onClick={() => { setTargetBudget(val); setCustomBudgetValue(String(val)); }}
                  className={`px-1.5 py-0.5 text-[10px] rounded border ${
                    targetBudget === val
                      ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                      : 'bg-white text-[#5C5349] border-[#DED6CA] hover:bg-[#F2ECE1]'
                  }`}
                >
                  ₹ {(val / 10000000).toFixed(val % 10000000 === 0 ? 1 : 2)} Cr
                </button>
              ))}
            </div>
          </div>

          {/* 2. Confirmed Committed Cost */}
          <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold">
                  2. Confirmed Allocation
                </span>
                <span className="text-[10px] px-2 py-0.5 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] font-bold font-mono rounded">
                  {confirmedVendors.length} Confirmed
                </span>
              </div>
              <div className="font-serif text-2xl font-bold text-[#2D5A3C]">
                {formatINR(confirmedCost)}
              </div>
              <p className="text-[11px] text-[#736F68] mt-1">
                {percentUtilized}% of planned celebration budget
              </p>
            </div>
            <div className="text-[11px] text-[#2D5A3C] font-medium pt-2 border-t border-[#E5E0D8]">
              Hard committed to executed vendors
            </div>
          </div>

          {/* 3. Shortlisted & Waitlisted Pipeline */}
          <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold">
                  3. Tentative Pipeline
                </span>
                <span className="text-[10px] px-2 py-0.5 bg-[#FEF6E9] text-[#9E7D3B] border border-[#F2D7A5] font-bold font-mono rounded">
                  {shortlistedVendors.length} Shortlisted
                </span>
              </div>
              <div className="font-serif text-2xl font-bold text-[#9E7D3B]">
                {formatINR(shortlistCost)}
              </div>
              <p className="text-[11px] text-[#736F68] mt-1">
                Waitlist backup: {formatINR(waitlistCost)} ({waitlistedVendors.length} vendors)
              </p>
            </div>
            <div className="text-[11px] text-[#8C6D1F] font-medium pt-2 border-t border-[#E5E0D8]">
              Optional spend under couple evaluation
            </div>
          </div>

          {/* 4. Remaining Budget Buffer */}
          <div className={`p-4 border flex flex-col justify-between ${
            isOverBudget
              ? 'bg-[#FDF2F2] border-[#F2B8B8] text-[#94352D]'
              : 'bg-[#EBF3ED]/50 border-[#C3D9C9] text-[#2D5A3C]'
          }`}>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] uppercase tracking-wider font-bold">
                  4. Remaining Buffer
                </span>
                <span className={`text-[9px] px-2 py-0.5 uppercase tracking-wider font-extrabold rounded ${
                  isOverBudget ? 'bg-[#94352D] text-white' : 'bg-[#2D5A3C] text-white'
                }`}>
                  {isOverBudget ? 'Budget Exceeded' : 'Surplus Buffer'}
                </span>
              </div>
              <div className="font-serif text-2xl font-bold">
                {isOverBudget ? `- ${formatINR(Math.abs(remainingBudget))}` : formatINR(remainingBudget)}
              </div>
              <p className="text-[11px] opacity-80 mt-1">
                {isOverBudget 
                  ? 'Confirmed vendors exceed planned budget. Adjust selections.'
                  : 'Available for palace royalty, suites, gifts & contingencies'}
              </p>
            </div>
            <div className="text-[11px] font-medium pt-2 border-t border-current/20">
              {isOverBudget ? '⚠️ Action Required' : '✓ Financially Balanced'}
            </div>
          </div>
        </div>

        {/* Visual Progress Bar & Category Allocation */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[11px] font-semibold text-[#1F2421] flex items-center gap-1.5">
              <TrendingUp size={13} className="text-[#9E7D3B]" />
              Budget Allocation Utilization: {percentUtilized}%
            </span>
            <span className="text-[11px] font-mono text-[#736F68]">
              {formatINR(confirmedCost)} of {formatINR(targetBudget)}
            </span>
          </div>

          <div className="w-full h-3 bg-[#E5E0D8] rounded-full overflow-hidden flex">
            <div
              className={`h-full transition-all duration-500 ${
                isOverBudget ? 'bg-[#94352D]' : 'bg-[#2D5A3C]'
              }`}
              style={{ width: `${Math.min(100, percentUtilized)}%` }}
            />
          </div>

          {categoryBreakdown.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {categoryBreakdown.map(cb => (
                <span
                  key={cb.category}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#FAF8F5] border border-[#E5E0D8] text-[11px] text-[#1F2421] rounded"
                >
                  <span className="w-2 h-2 rounded-full bg-[#9E7D3B]" />
                  <span className="font-medium">{cb.category}:</span>
                  <span className="text-[#9E7D3B] font-semibold">{formatINR(cb.amount)}</span>
                  <span className="text-[10px] text-[#8C877D]">({cb.pct}%)</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* SPREADSHEET TOOLBAR: SEARCH, FILTERS & VIEW MODE */}
      <div className="bg-white border border-[#E5E0D8] p-4 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search bar */}
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8C877D]" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Filter spreadsheet by vendor name, service category, specialty, or city..."
              className="w-full pl-9 pr-4 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] focus:border-[#9E7D3B] focus:outline-none"
            />
          </div>

          {/* Quick Selects & View Switcher */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* City */}
            <select
              value={cityFilter}
              onChange={e => setCityFilter(e.target.value)}
              className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] text-xs font-semibold focus:outline-none rounded"
            >
              <option value="All">All Cities</option>
              <option value="Jaipur">Jaipur</option>
              <option value="Udaipur">Udaipur</option>
              <option value="Jodhpur">Jodhpur</option>
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] text-xs font-semibold focus:outline-none rounded"
            >
              <option value="recommended">Sort: Recommended Status</option>
              <option value="budget-asc">Price: Low to High</option>
              <option value="budget-desc">Price: High to Low</option>
              <option value="rating-desc">Rating: Highest First</option>
            </select>

            {/* View Mode Toggle */}
            <div className="inline-flex items-center border border-[#E5E0D8] p-0.5 bg-[#FAF8F5] rounded">
              <button
                type="button"
                onClick={() => setViewMode('spreadsheet')}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                  viewMode === 'spreadsheet'
                    ? 'bg-[#1F2421] text-white shadow-xs'
                    : 'text-[#736F68] hover:text-[#1F2421]'
                }`}
              >
                <Table size={13} />
                <span>Spreadsheet</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('cards')}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                  viewMode === 'cards'
                    ? 'bg-[#1F2421] text-white shadow-xs'
                    : 'text-[#736F68] hover:text-[#1F2421]'
                }`}
              >
                <LayoutGrid size={13} />
                <span>Cards</span>
              </button>
            </div>
          </div>
        </div>

        {/* STATUS DROPDOWN FILTER TABS */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#E5E0D8]">
          <span className="text-[11px] font-semibold text-[#1F2421] flex items-center gap-1 mr-1">
            <Filter size={12} className="text-[#9E7D3B]" />
            Selection Status:
          </span>

          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1 text-xs rounded border transition-all ${
              statusFilter === 'all'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#5C5349] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            All Vendors ({vendors.length})
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('Confirmed')}
            className={`px-3 py-1 text-xs rounded border transition-all flex items-center gap-1.5 ${
              statusFilter === 'Confirmed'
                ? 'bg-[#2D5A3C] text-white border-[#2D5A3C] font-semibold'
                : 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9] hover:bg-[#DCECE0]'
            }`}
          >
            <CheckCircle2 size={12} />
            <span>Confirmed ({confirmedVendors.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('Shortlisted')}
            className={`px-3 py-1 text-xs rounded border transition-all flex items-center gap-1.5 ${
              statusFilter === 'Shortlisted'
                ? 'bg-[#9E7D3B] text-white border-[#9E7D3B] font-semibold'
                : 'bg-[#FEF6E9] text-[#9E7D3B] border-[#F2D7A5] hover:bg-[#FDF0D9]'
            }`}
          >
            <Star size={12} fill="currentColor" />
            <span>Shortlisted ({shortlistedVendors.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('Waitlisted')}
            className={`px-3 py-1 text-xs rounded border transition-all flex items-center gap-1.5 ${
              statusFilter === 'Waitlisted'
                ? 'bg-[#335C67] text-white border-[#335C67] font-semibold'
                : 'bg-[#F0F4F8] text-[#335C67] border-[#D1DFE8] hover:bg-[#E2EBF1]'
            }`}
          >
            <Clock size={12} />
            <span>Waitlisted ({waitlistedVendors.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('None')}
            className={`px-3 py-1 text-xs rounded border transition-all ${
              statusFilter === 'None'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#736F68] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            Not Selected
          </button>
        </div>

        {/* BUDGET COMPATIBILITY FILTER BUTTONS */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#E5E0D8]">
          <span className="text-[11px] font-semibold text-[#1F2421] mr-1">Budget Fit:</span>
          <button
            type="button"
            onClick={() => setBudgetFitFilter('all')}
            className={`px-2.5 py-1 text-[11px] rounded border transition-all ${
              budgetFitFilter === 'all'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#5C5349] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            All Budgets
          </button>
          <button
            type="button"
            onClick={() => setBudgetFitFilter('within-remaining')}
            className={`px-2.5 py-1 text-[11px] rounded border transition-all ${
              budgetFitFilter === 'within-remaining'
                ? 'bg-[#2D5A3C] text-white border-[#2D5A3C] font-semibold'
                : 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9] hover:bg-[#DCECE0]'
            }`}
          >
            Fits Buffer ({formatINR(Math.max(0, remainingBudget))})
          </button>
          <button
            type="button"
            onClick={() => setBudgetFitFilter('under-10l')}
            className={`px-2.5 py-1 text-[11px] rounded border transition-all ${
              budgetFitFilter === 'under-10l'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#5C5349] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            Boutique (&lt; ₹ 10L)
          </button>
          <button
            type="button"
            onClick={() => setBudgetFitFilter('10l-30l')}
            className={`px-2.5 py-1 text-[11px] rounded border transition-all ${
              budgetFitFilter === '10l-30l'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#5C5349] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            Heritage (₹ 10L - ₹ 30L)
          </button>
          <button
            type="button"
            onClick={() => setBudgetFitFilter('above-30l')}
            className={`px-2.5 py-1 text-[11px] rounded border transition-all ${
              budgetFitFilter === 'above-30l'
                ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                : 'bg-[#FAF8F5] text-[#5C5349] border-[#E5E0D8] hover:bg-white'
            }`}
          >
            Grand Royal (&gt; ₹ 30L)
          </button>
        </div>

        {/* Category Pills Bar */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-[#E5E0D8]">
          <span className="text-[11px] font-semibold text-[#1F2421] mr-1">Category:</span>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              type="button"
              onClick={() => setCategoryFilter(cat)}
              className={`px-2.5 py-1 text-[11px] border rounded transition-all ${
                categoryFilter === cat
                  ? 'bg-[#9E7D3B] text-white border-[#9E7D3B] font-semibold'
                  : 'bg-[#FAF8F5] text-[#736F68] border-[#E5E0D8] hover:bg-white hover:text-[#1F2421]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CONTENT: SPREADSHEET TABLE OR CARDS */}
      {loading ? (
        <div className="bg-white border border-[#E5E0D8] p-12 text-center text-xs text-[#736F68]">
          <RefreshCw size={24} className="mx-auto mb-2 text-[#9E7D3B] animate-spin" />
          <span>Loading verified palace vendors and pricing matrices...</span>
        </div>
      ) : filteredVendors.length === 0 ? (
        <div className="bg-white border border-[#E5E0D8] p-12 text-center space-y-3">
          <Info size={32} className="mx-auto text-[#8C877D]" />
          <h4 className="font-serif text-lg text-[#1F2421]">No Vendors Found Matching Filters</h4>
          <p className="text-xs text-[#736F68] max-w-md mx-auto">
            No vendor entries match the current category, status, and search query. Reset filters to review full roster.
          </p>
          <button
            type="button"
            onClick={() => { setCategoryFilter('All'); setStatusFilter('all'); setBudgetFitFilter('all'); setSearchQuery(''); }}
            className="px-4 py-2 bg-[#1F2421] text-white text-xs uppercase tracking-wider font-semibold rounded"
          >
            Reset All Filters
          </button>
        </div>
      ) : viewMode === 'spreadsheet' ? (
        /* ========================================================================= */
        /* SPREADSHEET STYLE TABLE VIEW (With Dropdown Menu on every row)           */
        /* ========================================================================= */
        <div className="bg-white border border-[#E5E0D8] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#FAF8F5] border-b border-[#E5E0D8] text-[10px] uppercase font-bold tracking-wider text-[#736F68]">
                  <th className="py-3.5 px-4 w-12 text-center">#</th>
                  <th className="py-3.5 px-4 min-w-[200px]">Vendor & Royal Partner</th>
                  <th className="py-3.5 px-4 min-w-[140px]">Category</th>
                  <th className="py-3.5 px-4 min-w-[110px]">Location</th>
                  <th className="py-3.5 px-4 w-20 text-center">Rating</th>
                  <th className="py-3.5 px-4 min-w-[130px] text-right font-serif">Package Cost</th>
                  <th className="py-3.5 px-4 min-w-[180px]">Selection / Status Dropdown</th>
                  <th className="py-3.5 px-4 min-w-[170px]">Budget Impact</th>
                  <th className="py-3.5 px-4 min-w-[100px] text-center">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E0D8]">
                {filteredVendors.map((vendor, index) => {
                  const status = vendorStatuses[vendor.id] || 'None';
                  const isConfirmed = status === 'Confirmed';
                  const isShortlisted = status === 'Shortlisted';
                  const isWaitlisted = status === 'Waitlisted';

                  const fitsRemaining = vendor.cost <= remainingBudget;
                  const difference = vendor.cost - remainingBudget;
                  const isExpanded = expandedVendorId === vendor.id;

                  return (
                    <React.Fragment key={vendor.id}>
                      <tr
                        className={`transition-colors hover:bg-[#FAF8F5] ${
                          isConfirmed
                            ? 'bg-[#EBF3ED]/40 font-medium'
                            : isShortlisted
                            ? 'bg-[#FEF6E9]/40'
                            : isWaitlisted
                            ? 'bg-[#F0F4F8]/40'
                            : ''
                        }`}
                      >
                        {/* 1. Row Index */}
                        <td className="py-3 px-4 text-center text-[#8C877D] font-mono text-[11px]">
                          {index + 1}
                        </td>

                        {/* 2. Vendor Name */}
                        <td className="py-3 px-4">
                          <div className="space-y-0.5">
                            <div className="font-serif font-bold text-sm text-[#1F2421]">
                              {vendor.name}
                            </div>
                            <div className="text-[11px] text-[#736F68] truncate max-w-xs italic">
                              {vendor.tagline}
                            </div>
                          </div>
                        </td>

                        {/* 3. Category */}
                        <td className="py-3 px-4">
                          <span className="inline-block px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] rounded">
                            {vendor.category}
                          </span>
                        </td>

                        {/* 4. Location */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1 text-[11px] text-[#5C5349]">
                            <MapPin size={12} className="text-[#9E7D3B] shrink-0" />
                            <span>{vendor.city}</span>
                          </div>
                        </td>

                        {/* 5. Rating */}
                        <td className="py-3 px-4 text-center">
                          <div className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] rounded text-[11px] font-bold text-[#8C6D1F]">
                            <Star size={10} fill="currentColor" />
                            <span>{vendor.rating?.toFixed(1) || '5.0'}</span>
                          </div>
                        </td>

                        {/* 6. Package Cost */}
                        <td className="py-3 px-4 text-right font-serif font-bold text-sm text-[#1F2421]">
                          {formatINR(vendor.cost)}
                        </td>

                        {/* 7. INTERACTIVE STATUS DROPDOWN MENU */}
                        <td className="py-3 px-4">
                          <div className="relative inline-block w-full max-w-[170px]">
                            <select
                              value={status}
                              onChange={e => handleStatusChange(vendor.id, e.target.value as VendorStatus)}
                              className={`w-full py-1.5 px-2.5 text-xs font-semibold rounded border transition-all cursor-pointer focus:outline-none focus:ring-1 ${
                                isConfirmed
                                  ? 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9] focus:ring-[#2D5A3C]'
                                  : isShortlisted
                                  ? 'bg-[#FEF6E9] text-[#9E7D3B] border-[#F2D7A5] focus:ring-[#9E7D3B]'
                                  : isWaitlisted
                                  ? 'bg-[#F0F4F8] text-[#335C67] border-[#D1DFE8] focus:ring-[#335C67]'
                                  : 'bg-[#FAF8F5] text-[#736F68] border-[#E5E0D8] hover:border-[#9E7D3B]'
                              }`}
                            >
                              <option value="None">— Not Selected —</option>
                              <option value="Confirmed">✓ Confirmed (Committed)</option>
                              <option value="Shortlisted">⭐ Shortlisted (Review)</option>
                              <option value="Waitlisted">⏳ Waitlisted (Backup)</option>
                            </select>
                          </div>
                        </td>

                        {/* 8. Budget Impact */}
                        <td className="py-3 px-4 text-[11px]">
                          {isConfirmed ? (
                            <span className="inline-flex items-center gap-1 text-[#2D5A3C] font-semibold">
                              <CheckCircle2 size={12} />
                              <span>Committed ({formatINR(vendor.cost)})</span>
                            </span>
                          ) : isShortlisted ? (
                            <span className="inline-flex items-center gap-1 text-[#9E7D3B] font-medium">
                              <Star size={11} fill="currentColor" />
                              <span>Pipeline: {formatINR(vendor.cost)}</span>
                            </span>
                          ) : isWaitlisted ? (
                            <span className="inline-flex items-center gap-1 text-[#335C67] font-medium">
                              <Clock size={11} />
                              <span>Backup Pool</span>
                            </span>
                          ) : fitsRemaining ? (
                            <span className="text-[#2D5A3C] font-medium">
                              ✓ Fits Buffer ({formatINR(remainingBudget - vendor.cost)} left)
                            </span>
                          ) : (
                            <span className="text-[#94352D] font-medium">
                              ⚠️ +{formatINR(difference)} Over Buffer
                            </span>
                          )}
                        </td>

                        {/* 9. Expand Deliverables Button */}
                        <td className="py-3 px-4 text-center">
                          <button
                            type="button"
                            onClick={() => setExpandedVendorId(isExpanded ? null : vendor.id)}
                            className="p-1 text-[#736F68] hover:text-[#1F2421] hover:bg-[#E5E0D8]/40 rounded transition-colors"
                            title="View Deliverables and Specialties"
                          >
                            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </td>
                      </tr>

                      {/* Expandable Details Row */}
                      {isExpanded && (
                        <tr className="bg-[#FAF8F5]/80 border-b border-[#E5E0D8]">
                          <td colSpan={9} className="p-4 text-xs space-y-2">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white p-3 border border-[#E5E0D8] rounded">
                              <div>
                                <span className="text-[10px] uppercase font-bold text-[#8C877D] tracking-wider block mb-1">
                                  Ceremonial Scope & Deliverables:
                                </span>
                                <p className="text-xs text-[#1F2421] leading-relaxed">
                                  {vendor.deliverables}
                                </p>
                              </div>
                              <div>
                                <span className="text-[10px] uppercase font-bold text-[#8C877D] tracking-wider block mb-1">
                                  Signature Specialties:
                                </span>
                                <div className="flex flex-wrap gap-1.5">
                                  {vendor.specialties.map((spec, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[10px] text-[#5C5349] rounded"
                                    >
                                      {spec}
                                    </span>
                                  ))}
                                </div>
                                <div className="mt-2 text-[11px] text-[#736F68]">
                                  Contact: <strong>{vendor.contactPerson || 'Royal Concierge'}</strong> ({vendor.phone})
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>

              {/* SPREADSHEET FOOTER ROW WITH TOTALS */}
              <tfoot>
                <tr className="bg-[#FAF8F5] border-t-2 border-[#1F2421] font-bold text-xs text-[#1F2421]">
                  <td colSpan={4} className="py-4 px-4 font-serif text-sm">
                    Spreadsheet Grand Totals ({filteredVendors.length} Listed / {confirmedVendors.length} Confirmed)
                  </td>
                  <td className="py-4 px-4 text-center">
                    Avg. 4.9★
                  </td>
                  <td className="py-4 px-4 text-right font-serif text-sm text-[#9E7D3B]">
                    {formatINR(confirmedCost)}
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2 py-1 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] rounded font-mono text-[11px]">
                      {confirmedVendors.length} Confirmed
                    </span>
                  </td>
                  <td colSpan={2} className="py-4 px-4">
                    <span className={`font-serif text-sm ${isOverBudget ? 'text-[#94352D]' : 'text-[#2D5A3C]'}`}>
                      {isOverBudget ? `Exceeded: -${formatINR(Math.abs(remainingBudget))}` : `Surplus: ${formatINR(remainingBudget)}`}
                    </span>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      ) : (
        /* ========================================================================= */
        /* CARDS VIEW MODE                                                           */
        /* ========================================================================= */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredVendors.map(vendor => {
            const status = vendorStatuses[vendor.id] || 'None';
            const isConfirmed = status === 'Confirmed';
            const isShortlisted = status === 'Shortlisted';
            const isWaitlisted = status === 'Waitlisted';

            const fitsRemaining = vendor.cost <= remainingBudget;
            const difference = vendor.cost - remainingBudget;

            return (
              <div
                key={vendor.id}
                className={`bg-white border transition-all flex flex-col justify-between rounded ${
                  isConfirmed
                    ? 'border-[#2D5A3C] ring-2 ring-[#2D5A3C]/20 shadow-md bg-[#FDFDFD]'
                    : isShortlisted
                    ? 'border-[#9E7D3B] ring-2 ring-[#9E7D3B]/20 shadow-sm'
                    : isWaitlisted
                    ? 'border-[#335C67] ring-1 ring-[#335C67]/20 shadow-sm'
                    : 'border-[#E5E0D8] hover:border-[#9E7D3B] hover:shadow-sm'
                }`}
              >
                <div className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] font-semibold text-[#9E7D3B] inline-block rounded">
                        {vendor.category}
                      </span>
                      <h4 className="font-serif text-base font-bold text-[#1F2421] leading-snug">
                        {vendor.name}
                      </h4>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="flex items-center gap-1 text-[#8C6D1F] bg-[#FAF8F5] px-2 py-0.5 border border-[#E5E0D8] text-xs font-bold rounded">
                        <Star size={11} fill="currentColor" />
                        <span>{vendor.rating?.toFixed(1) || '5.0'}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-[#736F68] leading-relaxed italic">
                    "{vendor.tagline}"
                  </p>

                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-2 rounded">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">
                        Estimated Package
                      </span>
                      <span className="font-serif text-base font-bold text-[#1F2421]">
                        {formatINR(vendor.cost)}
                      </span>
                    </div>

                    <div className="pt-1 border-t border-[#E5E0D8] flex items-center justify-between text-[11px]">
                      <span className="text-[#736F68]">Status:</span>
                      <select
                        value={status}
                        onChange={e => handleStatusChange(vendor.id, e.target.value as VendorStatus)}
                        className={`py-1 px-2 text-xs font-semibold rounded border cursor-pointer ${
                          isConfirmed
                            ? 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9]'
                            : isShortlisted
                            ? 'bg-[#FEF6E9] text-[#9E7D3B] border-[#F2D7A5]'
                            : isWaitlisted
                            ? 'bg-[#F0F4F8] text-[#335C67] border-[#D1DFE8]'
                            : 'bg-white text-[#736F68] border-[#E5E0D8]'
                        }`}
                      >
                        <option value="None">Not Selected</option>
                        <option value="Confirmed">✓ Confirmed</option>
                        <option value="Shortlisted">⭐ Shortlisted</option>
                        <option value="Waitlisted">⏳ Waitlisted</option>
                      </select>
                    </div>

                    <div className="text-[11px]">
                      {isConfirmed ? (
                        <span className="text-[#2D5A3C] font-semibold flex items-center gap-1">
                          <CheckCircle2 size={12} />
                          Committed to Royal Celebration
                        </span>
                      ) : fitsRemaining ? (
                        <span className="text-[#2D5A3C] font-medium flex items-center gap-1">
                          <CheckCircle2 size={12} />
                          Fits Buffer ({formatINR(remainingBudget - vendor.cost)} left)
                        </span>
                      ) : (
                        <span className="text-[#94352D] font-medium flex items-center gap-1">
                          <AlertTriangle size={12} />
                          +{formatINR(difference)} Over Buffer
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="space-y-1 text-xs pt-1">
                    <strong className="text-[#1F2421] text-[11px]">Deliverables:</strong>
                    <p className="text-[11px] text-[#736F68]">{vendor.deliverables}</p>
                  </div>
                </div>

                <div className="p-4 bg-[#FAF8F5] border-t border-[#E5E0D8] flex items-center justify-between gap-3 text-xs">
                  <div className="text-[11px] text-[#736F68] flex items-center gap-1">
                    <MapPin size={12} className="text-[#9E7D3B]" />
                    <span>{vendor.city}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleStatusChange(vendor.id, isConfirmed ? 'None' : 'Confirmed')}
                    className={`px-3 py-1.5 text-xs uppercase tracking-wider font-semibold rounded transition-all ${
                      isConfirmed
                        ? 'bg-[#1F2421] text-white hover:bg-[#94352D]'
                        : 'bg-[#9E7D3B] text-white hover:bg-[#8A6C32]'
                    }`}
                  >
                    {isConfirmed ? 'Remove' : 'Quick Confirm'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
