import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import {
  Heart,
  Building2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

const EVENT_OPTIONS = [
  'Welcome Dinner & Rajasthani Mehendi',
  'Royal Sangeet & Musical Extravaganza',
  'Haldi & Phoolon Ki Holi',
  'Sacred Vedic Mandap & Pheras',
  'Grand Royal Reception Banquet',
  'Post-Wedding Brunch & Lake Cruise',
];

const VENUE_OPTIONS = [
  'The Leela Palace, Udaipur',
  'Taj Lake Palace, Udaipur',
  'Jagmandir Island Palace, Udaipur',
  'Rambagh Palace, Jaipur',
  'Jai Mahal Palace, Jaipur',
  'Umaid Bhawan Palace, Jodhpur',
  'Fairmont Jaipur & Aravali Pavilions',
  'Custom Heritage Palace Estate',
];

const THEME_OPTIONS = [
  'Regal Rajputana Heritage & Floating Palace Splendor',
  'Mughal Opulence & Sheesh Mahal Aesthetics',
  'Contemporary Minimalist Heritage Luxury',
  'Lake Pichola Waterfront Romance & Lantern Glow',
  'Desert Mirage & Starlit Fortress Pageantry',
];

const PACKAGE_OPTIONS = [
  {
    id: 'Full-Service',
    title: 'Full-Service Royal Production',
    desc: 'End-to-end master design, royal palace liaisons, hospitality, bespoke decor & luxury banquet curation.'
  },
  {
    id: 'Partial-Service',
    title: 'Concierge & Production Direction',
    desc: 'Curated vendor management, styling architecture, and on-ground celebration execution.'
  },
  {
    id: 'Day-of Coordination',
    title: 'Venue & Royal Hospitality Management',
    desc: 'Dedicated focus on palace logistics, royal guest transfers, and ceremonial coordination.'
  },
];

export const ClientIntakePage: React.FC = () => {
  const { currentUser, setHasCompletedDetails, setAgreementId } = useClients();
  const navigate = useNavigate();

  // Form State
  const [partner1Name, setPartner1Name] = useState(currentUser.name || '');
  const [partner2Name, setPartner2Name] = useState('');
  const [email, setEmail] = useState(currentUser.email || '');
  const [phone, setPhone] = useState('+91 98765 43210');
  const [weddingDate, setWeddingDate] = useState('2026-11-15');
  const [weddingLocation, setWeddingLocation] = useState('The Leela Palace, Udaipur');
  const [expectedGuestCount, setExpectedGuestCount] = useState<number>(200);
  const [estimatedBudget, setEstimatedBudget] = useState<number>(25000000);
  const [selectedEvents, setSelectedEvents] = useState<string[]>([
    'Welcome Dinner & Rajasthani Mehendi',
    'Royal Sangeet & Musical Extravaganza',
    'Sacred Vedic Mandap & Pheras',
    'Grand Royal Reception Banquet'
  ]);
  const [weddingTheme, setWeddingTheme] = useState('Regal Rajputana Heritage & Floating Palace Splendor');
  const [servicePackage, setServicePackage] = useState<'Full-Service' | 'Partial-Service' | 'Day-of Coordination'>('Full-Service');
  const [additionalRequirements, setAdditionalRequirements] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If client already has a record in backend, try to pre-fill
    if (currentUser.clientId) {
      fetch(`/api/v1/clients/${currentUser.clientId}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data) {
            if (data.partner1_name) setPartner1Name(data.partner1_name);
            if (data.partner2_name && data.partner2_name !== 'Partner') setPartner2Name(data.partner2_name);
            if (data.email) setEmail(data.email);
            if (data.phone) setPhone(data.phone);
            if (data.wedding_date) setWeddingDate(data.wedding_date);
            if (data.wedding_location) setWeddingLocation(data.wedding_location);
            if (data.expected_guest_count) setExpectedGuestCount(data.expected_guest_count);
            if (data.estimated_budget) setEstimatedBudget(Number(data.estimated_budget));
            if (data.wedding_theme) setWeddingTheme(data.wedding_theme);
            if (data.service_package) setServicePackage(data.service_package);
            if (data.additional_requirements) setAdditionalRequirements(data.additional_requirements);
          }
        })
        .catch(() => {});
    }
  }, [currentUser.clientId]);

  const toggleEvent = (event: string) => {
    if (selectedEvents.includes(event)) {
      setSelectedEvents(selectedEvents.filter(e => e !== event));
    } else {
      setSelectedEvents([...selectedEvents, event]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!partner1Name.trim()) {
      setError('Please provide the primary partner name.');
      return;
    }
    if (!partner2Name.trim()) {
      setError("Please provide your partner's full name.");
      return;
    }
    if (!weddingDate) {
      setError('Please select your target wedding celebration date.');
      return;
    }
    if (!weddingLocation.trim()) {
      setError('Please select or specify your preferred palace destination.');
      return;
    }

    setIsSubmitting(true);

    try {
      let clientId = currentUser.clientId || localStorage.getItem('the_royal_knot_client_id_v1') || undefined;
      const clientEmail = email.trim().toLowerCase();
      const payload = {
        partner1Name: partner1Name.trim(),
        partner2Name: partner2Name.trim(),
        email: clientEmail,
        phone: phone.trim(),
        weddingDate,
        weddingLocation: weddingLocation.trim(),
        expectedGuestCount: Number(expectedGuestCount) || 150,
        estimatedBudget: Number(estimatedBudget) || 25000000,
        weddingTheme,
        servicePackage,
        additionalRequirements: additionalRequirements.trim() || undefined,
        status: 'Agreement Pending'
      };

      // If clientId is not set, try finding by email
      if (!clientId && clientEmail) {
        try {
          const sRes = await fetch(`/api/v1/clients/search?query=${encodeURIComponent(clientEmail)}`);
          if (sRes.ok) {
            const sData = await sRes.json();
            const match = sData.items?.find((c: any) => c.email.toLowerCase() === clientEmail);
            if (match) clientId = match.id;
          }
        } catch (_) {}
      }

      if (clientId) {
        // Update client dossier in backend
        const res = await fetch(`/api/v1/clients/${clientId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Failed to save celebration details.');
        }
      } else {
        // Create new client record if not already present
        const cRes = await fetch('/api/v1/clients', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (cRes.ok) {
          const cData = await cRes.json();
          if (cData && cData.id) {
            clientId = cData.id;
          }
        }
      }

      if (clientId) {
        localStorage.setItem('the_royal_knot_client_id_v1', clientId);
        // Fetch or create agreement for client
        try {
          const agrRes = await fetch(`/api/v1/agreements/client/${clientId}`);
          if (agrRes.ok) {
            const agrData = await agrRes.json();
            if (agrData && agrData.id) {
              setAgreementId(agrData.id);
            }
          }
        } catch (_) {}
      }

      // Mark details intake completed
      setHasCompletedDetails(true);

      // Smoothly advance to Service Agreement
      navigate('/agreement');
    } catch (err: any) {
      setError(err.message || 'Unable to save your details. Please check connection and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] py-10 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium mb-2">
            <span>✦</span>
            <span>The Royal Knot Concierge</span>
            <span>✦</span>
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl text-[#1F2421] font-normal uppercase tracking-wider">
            Client Wedding Intake Dossier
          </h1>
          <p className="text-xs uppercase tracking-[0.2em] text-[#8C877D] mt-2">
            Step 1: Enter Celebration Details & Parameters Before Service Agreement
          </p>
        </div>

        {/* 3-Step Onboarding Roadmap Progress Bar */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 mb-8 shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="flex items-center gap-2.5 p-3 bg-[#FAF8F5] border-l-4 border-[#9E7D3B]">
              <div className="w-6 h-6 rounded-full bg-[#9E7D3B] text-white flex items-center justify-center font-bold text-[11px]">
                1
              </div>
              <div>
                <p className="font-semibold text-[#1F2421] uppercase tracking-wider text-[11px]">Wedding Details</p>
                <p className="text-[10px] text-[#9E7D3B] font-medium">In Progress (Active)</p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 p-3 bg-[#FFFFFF] border border-[#E5E0D8] opacity-75">
              <div className="w-6 h-6 rounded-full bg-[#E5E0D8] text-[#736F68] flex items-center justify-center font-bold text-[11px]">
                2
              </div>
              <div>
                <p className="font-semibold text-[#736F68] uppercase tracking-wider text-[11px]">Service Agreement</p>
                <p className="text-[10px] text-[#8C877D]">Next Stage</p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 p-3 bg-[#FFFFFF] border border-[#E5E0D8] opacity-50">
              <div className="w-6 h-6 rounded-full bg-[#E5E0D8] text-[#736F68] flex items-center justify-center font-bold text-[11px]">
                3
              </div>
              <div>
                <p className="font-semibold text-[#736F68] uppercase tracking-wider text-[11px]">Planning Portal</p>
                <p className="text-[10px] text-[#8C877D]">Final Access</p>
              </div>
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 mb-8 text-xs text-[#4A4640] leading-relaxed flex items-start gap-4 shadow-sm">
          <div className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] mt-0.5 shrink-0">
            <Sparkles className="w-5 h-5 stroke-[1.5]" />
          </div>
          <div>
            <h4 className="font-serif text-sm font-semibold uppercase tracking-wider text-[#1F2421] mb-1">
              Personalized Wedding Agreement Setup
            </h4>
            <p>
              Please enter your wedding parameters below. The details you provide here—including destination palace, wedding date, guest count, and service scope—will immediately be used to generate your official <strong>Service Agreement</strong> and payment milestone schedule.
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-[#FAF8F5] border border-red-200 text-red-800 p-4 mb-8 text-xs flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Intake Form */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Section 1: Couple & Contact Details */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#9E7D3B] mb-4 pb-2 border-b border-[#E5E0D8]">
              <Heart className="w-4 h-4" />
              <span>1. Couple & Contact Information</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Partner 1 Full Name *
                </label>
                <input
                  type="text"
                  value={partner1Name}
                  onChange={e => setPartner1Name(e.target.value)}
                  placeholder="e.g. Maharani Gayatri / Groom Name"
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Partner 2 Full Name *
                </label>
                <input
                  type="text"
                  value={partner2Name}
                  onChange={e => setPartner2Name(e.target.value)}
                  placeholder="e.g. Raja Man Singh / Bride Name"
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Primary Contact Email *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Contact Phone Number *
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Destination Wedding Parameters */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#9E7D3B] mb-4 pb-2 border-b border-[#E5E0D8]">
              <Building2 className="w-4 h-4" />
              <span>2. Destination Wedding Parameters</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Target Wedding Celebration Date *
                </label>
                <input
                  type="date"
                  value={weddingDate}
                  onChange={e => setWeddingDate(e.target.value)}
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Preferred Palace Venue & Destination *
                </label>
                <select
                  value={weddingLocation}
                  onChange={e => setWeddingLocation(e.target.value)}
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                >
                  {VENUE_OPTIONS.map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Expected Guest Count *
                </label>
                <input
                  type="number"
                  min={20}
                  max={5000}
                  value={expectedGuestCount}
                  onChange={e => setExpectedGuestCount(Number(e.target.value))}
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Estimated Celebration Budget (INR) *
                </label>
                <input
                  type="number"
                  min={500000}
                  step={100000}
                  value={estimatedBudget}
                  onChange={e => setEstimatedBudget(Number(e.target.value))}
                  required
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
                <span className="text-[10px] text-[#8C877D] mt-1 block">
                  e.g. ₹ {(estimatedBudget / 10000000).toFixed(2)} Cr
                </span>
              </div>
            </div>
          </div>

          {/* Section 3: Celebrations & Aesthetics */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#9E7D3B] mb-4 pb-2 border-b border-[#E5E0D8]">
              <Sparkles className="w-4 h-4" />
              <span>3. Ceremonies & Aesthetic Direction</span>
            </div>

            <div className="space-y-5 text-xs">
              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-2 font-medium">
                  Multi-Day Wedding Ceremonies
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {EVENT_OPTIONS.map(ev => {
                    const checked = selectedEvents.includes(ev);
                    return (
                      <button
                        type="button"
                        key={ev}
                        onClick={() => toggleEvent(ev)}
                        className={`text-left p-2.5 border text-xs flex items-center justify-between transition-colors ${
                          checked
                            ? 'bg-[#FAF8F5] border-[#9E7D3B] text-[#1F2421] font-medium'
                            : 'bg-white border-[#E5E0D8] text-[#736F68] hover:border-[#1F2421]'
                        }`}
                      >
                        <span>{ev}</span>
                        {checked && <CheckCircle2 size={14} className="text-[#9E7D3B] shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-2 font-medium">
                  Aesthetic Theme & Architectural Vision
                </label>
                <select
                  value={weddingTheme}
                  onChange={e => setWeddingTheme(e.target.value)}
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                >
                  {THEME_OPTIONS.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-2 font-medium">
                  Service Package Tier
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {PACKAGE_OPTIONS.map(pkg => {
                    const active = servicePackage === pkg.id;
                    return (
                      <div
                        key={pkg.id}
                        onClick={() => setServicePackage(pkg.id as any)}
                        className={`p-3.5 border cursor-pointer transition-all ${
                          active
                            ? 'border-[#9E7D3B] bg-[#FAF8F5] shadow-xs'
                            : 'border-[#E5E0D8] bg-white hover:border-[#736F68]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <p className={`font-semibold text-xs ${active ? 'text-[#1F2421]' : 'text-[#736F68]'}`}>
                            {pkg.title}
                          </p>
                          {active && <CheckCircle2 size={13} className="text-[#9E7D3B]" />}
                        </div>
                        <p className="text-[11px] text-[#736F68] leading-relaxed">{pkg.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-[#736F68] uppercase tracking-wider mb-1 font-medium">
                  Special Requirements & Hospitality Notes
                </label>
                <textarea
                  rows={3}
                  value={additionalRequirements}
                  onChange={e => setAdditionalRequirements(e.target.value)}
                  placeholder="e.g. Vegetarian Royal Feast, Shehnai Procession at Palace Gates, Helipad transfers..."
                  className="w-full p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>
            </div>
          </div>

          {/* Submission Bar */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs text-[#736F68]">
              <ShieldCheck size={16} className="text-[#9E7D3B]" />
              <span>Details will be instantly linked to your official Service Agreement.</span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-semibold border border-[#1F2421] transition-colors disabled:opacity-60"
            >
              <span>{isSubmitting ? 'GENERATING AGREEMENT...' : 'CONTINUE TO SERVICE AGREEMENT'}</span>
              <ArrowRight size={14} className="text-[#D9C496]" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default ClientIntakePage;
