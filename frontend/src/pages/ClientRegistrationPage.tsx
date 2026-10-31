import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { registrationApi } from '../services/api';
import {
  Heart,
  Calendar,
  Users,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Shield,
} from 'lucide-react';

const EVENT_OPTIONS = [
  'Welcome Dinner & Rajasthani Mehendi',
  'Royal Sangeet & Musical Extravaganza',
  'Haldi & Phoolon Ki Holi',
  'Sacred Vedic Mandap & Pheras',
  'Grand Royal Reception Banquet',
  'Post-Wedding Brunch & Lake Cruise',
];

const THEME_OPTIONS = [
  'Regal Rajputana Heritage & Floating Palace Splendor',
  'Mughal Opulence & Sheesh Mahal Aesthetics',
  'Contemporary Minimalist Heritage Luxury',
  'Lake Pichola Waterfront Romance & Lantern Glow',
  'Desert Mirage & Starlit Fortress Pageantry',
];

const PACKAGE_OPTIONS = [
  { id: 'Full-Service', title: 'Full-Service Royal Production', desc: 'End-to-end master design, royal palace liaisons, hospitality, decor & bespoke entertainment.' },
  { id: 'Partial-Concierge', title: 'Concierge & Production Direction', desc: 'Curated vendor management, styling architecture, and on-ground celebration execution.' },
  { id: 'Heritage-Venue', title: 'Venue & Royal Hospitality Management', desc: 'Dedicated focus on palace logistics, royal guest transfers, and ceremonial decor.' },
];

export const ClientRegistrationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [isLoading, setIsLoading] = useState(true);
  const [tokenInfo, setTokenInfo] = useState<{
    valid: boolean;
    message: string;
    enquiryId?: string;
    clientName?: string;
    partnerName?: string;
    email?: string;
    phone?: string;
    weddingDate?: string;
    weddingLocation?: string;
    expectedGuestCount?: number;
    estimatedBudget?: number;
    requirements?: string;
    existingRegistration?: any;
  } | null>(null);

  // Form State
  const [fullName, setFullName] = useState('');
  const [partnerName, setPartnerName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [weddingDate, setWeddingDate] = useState('');
  const [weddingLocation, setWeddingLocation] = useState('Udaipur / Lake Pichola Palaces');
  const [expectedGuestCount, setExpectedGuestCount] = useState<number | ''>(250);
  const [estimatedBudget, setEstimatedBudget] = useState<number | ''>(25000000);
  const [selectedEvents, setSelectedEvents] = useState<string[]>([
    'Welcome Dinner & Rajasthani Mehendi',
    'Royal Sangeet & Musical Extravaganza',
    'Sacred Vedic Mandap & Pheras',
    'Grand Royal Reception Banquet'
  ]);
  const [preferredTheme, setPreferredTheme] = useState('Regal Rajputana Heritage & Floating Palace Splendor');
  const [servicePackage, setServicePackage] = useState('Full-Service');
  const [preferences, setPreferences] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submittedData, setSubmittedData] = useState<any>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setTokenInfo({
        valid: false,
        message: 'No registration invitation token was found in the link. Please verify your invitation email.'
      });
      return;
    }

    const verify = async () => {
      try {
        const res = await registrationApi.verifyToken(token);
        setTokenInfo(res);

        if (res.valid) {
          // Pre-fill fields from existing registration or initial enquiry
          const reg = res.existingRegistration;
          setFullName(reg?.fullName || res.clientName || '');
          setPartnerName(reg?.partnerName || res.partnerName || '');
          setEmail(reg?.email || res.email || '');
          setPhone(reg?.phone || res.phone || '');
          setAddress(reg?.address || '');
          setWeddingDate(reg?.weddingDate || res.weddingDate || '');
          setWeddingLocation(reg?.weddingLocation || res.weddingLocation || 'Udaipur / Lake Pichola Palaces');
          setExpectedGuestCount(reg?.expectedGuestCount ?? res.expectedGuestCount ?? 250);
          setEstimatedBudget(reg?.estimatedBudget ?? res.estimatedBudget ?? 25000000);
          if (reg?.weddingEvents && Array.isArray(reg.weddingEvents)) {
            setSelectedEvents(reg.weddingEvents);
          }
          if (reg?.preferredTheme) setPreferredTheme(reg.preferredTheme);
          if (reg?.servicePackage) setServicePackage(reg.servicePackage);
          setPreferences(reg?.preferences || res.requirements || '');

          if (reg && (reg.status === 'APPROVED' || reg.status === 'SUBMITTED')) {
            setSubmittedData(reg);
          }
        }
      } catch (err: any) {
        setTokenInfo({
          valid: false,
          message: err.message || 'Unable to connect to The Royal Knot registration service.'
        });
      } finally {
        setIsLoading(false);
      }
    };

    verify();
  }, [token]);

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

    if (!fullName.trim()) {
      setError('Please provide your full legal name.');
      return;
    }
    if (!email.trim()) {
      setError('Please provide your primary contact email address.');
      return;
    }
    if (!phone.trim() || phone.trim().length < 7) {
      setError('Please enter a valid telephone number with country code.');
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        token,
        fullName: fullName.trim(),
        partnerName: partnerName.trim() || undefined,
        email: email.trim().toLowerCase(),
        phone: phone.trim(),
        address: address.trim() || undefined,
        weddingDate: weddingDate || undefined,
        weddingLocation: weddingLocation.trim() || undefined,
        expectedGuestCount: expectedGuestCount ? Number(expectedGuestCount) : undefined,
        estimatedBudget: estimatedBudget ? Number(estimatedBudget) : undefined,
        weddingEvents: selectedEvents,
        preferredTheme,
        servicePackage,
        preferences: preferences.trim() || undefined,
      };

      const res = await registrationApi.submitRegistration(payload);
      setSubmitSuccess(true);
      setSubmittedData({
        ...payload,
        status: res.status || 'SUBMITTED',
        submittedAt: res.submitted_at || new Date().toISOString()
      });
    } catch (err: any) {
      setError(err.message || 'Unable to submit your registration form. Please review the details and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex flex-col justify-center items-center p-6 text-center">
        <div className="w-12 h-12 border-2 border-[#9E7D3B] border-t-transparent animate-spin mb-4" />
        <h2 className="font-serif text-xl tracking-wider uppercase text-[#1F2421]">Verifying Invitation</h2>
        <p className="text-xs uppercase tracking-widest text-[#8C877D] mt-2">Connecting with The Royal Knot Concierge Desk...</p>
      </div>
    );
  }

  if (!tokenInfo?.valid) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex flex-col justify-center items-center p-6">
        <div className="w-full max-w-lg bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-12 text-center">
          <div className="w-14 h-14 mx-auto mb-6 bg-[#FAF8F5] border border-[#E5E0D8] flex items-center justify-center text-[#9E7D3B]">
            <AlertCircle className="w-7 h-7 stroke-[1.5]" />
          </div>
          <span className="text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium">Invitation Notice</span>
          <h1 className="font-serif text-2xl uppercase tracking-wider text-[#1F2421] mt-2 mb-4">Registration Link Invalid</h1>
          <p className="text-sm text-[#4A4640] leading-relaxed mb-6 font-sans">
            {tokenInfo?.message || 'This registration link has expired or is invalid. Each invitation link is cryptographically tied to a confidential wedding dossier.'}
          </p>
          <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#8C877D] mb-6 leading-relaxed">
            Need assistance? Please reach out to your designated wedding concierge directly at{' '}
            <strong className="text-[#1F2421]">saisubodh6@gmail.com</strong> or contact our Rajasthan operations desk.
          </div>
          <Link
            to="/login"
            className="inline-block px-8 py-3 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-medium hover:bg-[#2C332D] transition-colors"
          >
            Access Client Portal
          </Link>
        </div>
      </div>
    );
  }

  // If already submitted and showing confirmation
  if (submitSuccess || (submittedData && submittedData.status === 'APPROVED')) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex flex-col justify-center items-center p-6">
        <div className="w-full max-w-2xl bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-12 text-center shadow-sm">
          <div className="w-16 h-16 mx-auto mb-6 bg-[#FAF8F5] border border-[#9E7D3B]/40 flex items-center justify-center text-[#9E7D3B]">
            <CheckCircle2 className="w-8 h-8 stroke-[1.5]" />
          </div>

          <span className="text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium">✦ Dossier Secured ✦</span>
          <h1 className="font-serif text-3xl uppercase tracking-wider text-[#1F2421] mt-2 mb-3">
            Registration Received
          </h1>
          <p className="text-sm font-serif italic text-[#8C877D] mb-6">
            In honor of {fullName} {partnerName ? `& ${partnerName}` : ''}
          </p>

          <div className="text-left bg-[#FAF8F5] border border-[#E5E0D8] p-6 mb-8 text-xs text-[#4A4640] leading-relaxed space-y-3 font-sans">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#1F2421] border-b border-[#E5E0D8] pb-2">
              <Shield className="w-4 h-4 text-[#9E7D3B]" />
              <span>Dossier Submission Summary</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Reference Dossier</span>
                <span className="font-medium text-[#1F2421]">{tokenInfo.enquiryId}</span>
              </div>
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Registered Email</span>
                <span className="font-medium text-[#1F2421]">{email}</span>
              </div>
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Destination Hub</span>
                <span className="font-medium text-[#1F2421]">{weddingLocation}</span>
              </div>
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Target Date</span>
                <span className="font-medium text-[#1F2421]">{weddingDate || 'To be finalized'}</span>
              </div>
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Estimated Guests</span>
                <span className="font-medium text-[#1F2421]">{expectedGuestCount} Guests</span>
              </div>
              <div>
                <span className="text-[#8C877D] uppercase block text-[10px] tracking-wider">Selected Package</span>
                <span className="font-medium text-[#1F2421]">{servicePackage}</span>
              </div>
            </div>
          </div>

          <div className="bg-[#FFFFFF] border-l-2 border-[#9E7D3B] p-4 text-left text-xs text-[#4A4640] leading-relaxed mb-8">
            <strong className="text-[#1F2421] block uppercase tracking-wider text-[11px] mb-1">Next Step: Concierge Approval & Activation</strong>
            Our executive wedding directors are reviewing your celebration parameters. Once reviewed, an account activation link will be dispatched to <strong className="text-[#1F2421]">{email}</strong> to set your confidential password and unlock your planning suite.
          </div>

          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/login"
              className="px-8 py-3 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-medium hover:bg-[#2C332D] transition-colors"
            >
              Go to Portal Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Luxury Brand Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.3em] text-[#9E7D3B] font-medium mb-3">
            <span>✦</span>
            <span>The Royal Knot — Client Registration</span>
            <span>✦</span>
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl text-[#1F2421] font-normal uppercase tracking-wider">
            Bespoke Wedding Dossier
          </h1>
          <p className="text-xs uppercase tracking-[0.25em] text-[#8C877D] mt-2">
            Palace Celebrations · Jaipur & Udaipur · Ref: {tokenInfo.enquiryId}
          </p>
        </div>

        {/* Informational Banner */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 mb-8 text-xs text-[#4A4640] leading-relaxed flex items-start gap-4 shadow-sm">
          <div className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] mt-0.5 shrink-0">
            <Sparkles className="w-5 h-5 stroke-[1.5]" />
          </div>
          <div>
            <h4 className="font-serif text-sm font-semibold uppercase tracking-wider text-[#1F2421] mb-1">
              Welcome to Your Private Consultation Dossier
            </h4>
            <p>
              Please take a moment to complete your celebration preferences below. Any details already shared with our concierge have been pre-filled for your convenience. Upon employee review and approval, your confidential portal activation credentials will be dispatched to your email.
            </p>
          </div>
        </div>

        {/* Notice if corrections were previously requested */}
        {tokenInfo.existingRegistration?.status === 'CORRECTIONS_REQUESTED' && (
          <div className="bg-[#FFFDF7] border-l-4 border-[#9E7D3B] p-5 mb-8 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#9E7D3B] mb-2">
              <AlertCircle className="w-4 h-4" />
              <span>Director Feedback & Clarifications Requested</span>
            </div>
            <p className="text-xs text-[#4A4640] leading-relaxed whitespace-pre-wrap">
              {tokenInfo.existingRegistration.correctionNotes || 'Please review the celebration parameters below and submit your updated details.'}
            </p>
          </div>
        )}

        {/* Error notification */}
        {error && (
          <div className="bg-[#FAF8F5] border border-red-200 text-red-800 p-4 mb-8 text-xs flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* SECTION 1: COUPLE & CONTACT */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-3 border-b border-[#E5E0D8] pb-4 mb-6">
              <Heart className="w-5 h-5 text-[#9E7D3B] stroke-[1.5]" />
              <div>
                <h3 className="font-serif text-lg uppercase tracking-wider text-[#1F2421]">
                  1. The Couple & Primary Contact
                </h3>
                <p className="text-[11px] text-[#8C877D] uppercase tracking-wider">
                  Names as they will appear on bespoke palace stationery & formal contracts
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Client Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Princess Ananya Singh"
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Partner's Full Name
                </label>
                <input
                  type="text"
                  value={partnerName}
                  onChange={(e) => setPartnerName(e.target.value)}
                  placeholder="e.g. Yuvraj Devendra Rathore"
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Official Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  readOnly
                  className="w-full px-4 py-3 bg-[#F5F2ED] border border-[#E5E0D8] text-sm text-[#4A4640] cursor-not-allowed rounded-none font-mono text-xs"
                />
                <span className="text-[10px] text-[#8C877D] mt-1 block">Tied to enquiry verification. Cannot be altered.</span>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Telephone / Mobile *
                </label>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="e.g. +91 98290 12345"
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Mailing / Residential Address
                </label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="City, State, Country & Postal Code"
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: CELEBRATION PARAMETERS */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-3 border-b border-[#E5E0D8] pb-4 mb-6">
              <Calendar className="w-5 h-5 text-[#9E7D3B] stroke-[1.5]" />
              <div>
                <h3 className="font-serif text-lg uppercase tracking-wider text-[#1F2421]">
                  2. Destination Parameters & Logistics
                </h3>
                <p className="text-[11px] text-[#8C877D] uppercase tracking-wider">
                  Target celebration dates, palace venues, and guest estimates
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Target Wedding Date / Auspicious Month
                </label>
                <input
                  type="date"
                  value={weddingDate}
                  onChange={(e) => setWeddingDate(e.target.value)}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Preferred Palace City / Venue
                </label>
                <select
                  value={weddingLocation}
                  onChange={(e) => setWeddingLocation(e.target.value)}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                >
                  <option value="Udaipur / Lake Pichola Palaces">Udaipur (Jagmandir, Taj Lake Palace, Leela Pichola)</option>
                  <option value="Jaipur / Heritage Fortresses">Jaipur (Rambagh Palace, Samode, Fairmont, Jai Mahal)</option>
                  <option value="Jodhpur / Umaid Bhawan & Forts">Jodhpur (Umaid Bhawan, Mehrangarh, Mihir Garh)</option>
                  <option value="Jaisalmer / Thar Luxury Camps">Jaisalmer (Suryagarh, Jaisalmer Desert Enclaves)</option>
                  <option value="Multi-Destination Royal Tour">Multi-Destination Rajasthan Celebration</option>
                </select>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Estimated Royal Guest Count
                </label>
                <input
                  type="number"
                  min="20"
                  max="3000"
                  value={expectedGuestCount}
                  onChange={(e) => setExpectedGuestCount(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                />
                <span className="text-[10px] text-[#8C877D] mt-1 block">Includes both resident & visiting attendees.</span>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Estimated Celebration Budget (₹ INR)
                </label>
                <input
                  type="number"
                  step="500000"
                  value={estimatedBudget}
                  onChange={(e) => setEstimatedBudget(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors font-mono"
                />
                <span className="text-[10px] text-[#8C877D] mt-1 block">
                  {estimatedBudget ? `Approx ₹ ${(Number(estimatedBudget) / 10000000).toFixed(2)} Crores` : 'Enter figure in INR'}
                </span>
              </div>
            </div>
          </div>

          {/* SECTION 3: WEDDING FUNCTIONS & ITINERARY */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-3 border-b border-[#E5E0D8] pb-4 mb-6">
              <Users className="w-5 h-5 text-[#9E7D3B] stroke-[1.5]" />
              <div>
                <h3 className="font-serif text-lg uppercase tracking-wider text-[#1F2421]">
                  3. Ceremonial Functions & Events
                </h3>
                <p className="text-[11px] text-[#8C877D] uppercase tracking-wider">
                  Select all royal ceremonies to be orchestrated within your master schedule
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {EVENT_OPTIONS.map((event) => {
                const isChecked = selectedEvents.includes(event);
                return (
                  <div
                    key={event}
                    onClick={() => toggleEvent(event)}
                    className={`p-4 border cursor-pointer transition-all flex items-center justify-between ${
                      isChecked
                        ? 'bg-[#FAF8F5] border-[#9E7D3B] text-[#1F2421]'
                        : 'bg-[#FFFFFF] border-[#E5E0D8] text-[#8C877D] hover:border-[#C4BDB2]'
                    }`}
                  >
                    <span className="text-xs font-medium font-sans">{event}</span>
                    <div
                      className={`w-4 h-4 border flex items-center justify-center transition-colors ${
                        isChecked ? 'bg-[#9E7D3B] border-[#9E7D3B]' : 'border-[#C4BDB2]'
                      }`}
                    >
                      {isChecked && <div className="w-1.5 h-1.5 bg-white" />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SECTION 4: THEME & SERVICE TIER */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-3 border-b border-[#E5E0D8] pb-4 mb-6">
              <Sparkles className="w-5 h-5 text-[#9E7D3B] stroke-[1.5]" />
              <div>
                <h3 className="font-serif text-lg uppercase tracking-wider text-[#1F2421]">
                  4. Aesthetic Vision & Planning Tier
                </h3>
                <p className="text-[11px] text-[#8C877D] uppercase tracking-wider">
                  The visual tapestry and scope of agency orchestration
                </p>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Celebration Theme & Aesthetic Palette
                </label>
                <select
                  value={preferredTheme}
                  onChange={(e) => setPreferredTheme(e.target.value)}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors"
                >
                  {THEME_OPTIONS.map((theme) => (
                    <option key={theme} value={theme}>{theme}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Agency Retainer Tier
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {PACKAGE_OPTIONS.map((pkg) => {
                    const isSelected = servicePackage === pkg.id;
                    return (
                      <div
                        key={pkg.id}
                        onClick={() => setServicePackage(pkg.id)}
                        className={`p-4 border cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-[#FAF8F5] border-[#9E7D3B]'
                            : 'bg-[#FFFFFF] border-[#E5E0D8] hover:border-[#C4BDB2]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs uppercase tracking-wider font-semibold ${isSelected ? 'text-[#9E7D3B]' : 'text-[#1F2421]'}`}>
                            {pkg.id}
                          </span>
                          {isSelected && <div className="w-2 h-2 rounded-full bg-[#9E7D3B]" />}
                        </div>
                        <h5 className="font-serif text-xs font-medium text-[#1F2421] mb-1">{pkg.title}</h5>
                        <p className="text-[11px] text-[#8C877D] leading-relaxed">{pkg.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#1F2421] font-medium mb-2">
                  Confidential Preferences & Bespoke Requirements
                </label>
                <textarea
                  rows={4}
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  placeholder="Detail any specific culinary requirements, private aircraft charters, VIP security, royal processions, or heritage musical performers..."
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] text-sm text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] rounded-none transition-colors leading-relaxed"
                />
              </div>
            </div>
          </div>

          {/* PRIVACY & SUBMIT */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
            <div className="text-xs text-[#8C877D] leading-relaxed max-w-lg">
              <strong className="text-[#1F2421] uppercase tracking-wider block mb-1">Confidentiality Guarantee</strong>
              By submitting this dossier, your information is securely stored in our PostgreSQL database for review by authorized wedding directors. Account activation credentials will follow upon review.
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto px-10 py-4 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.25em] font-medium hover:bg-[#2C332D] transition-colors disabled:opacity-50 shrink-0 flex items-center justify-center gap-3"
            >
              {isSubmitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-[#FAF8F5] border-t-transparent animate-spin" />
                  <span>Securing Dossier...</span>
                </>
              ) : (
                <>
                  <span>Submit Registration</span>
                  <ArrowRight className="w-4 h-4 text-[#9E7D3B]" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
