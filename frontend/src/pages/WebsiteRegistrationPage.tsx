import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import {
  Sparkles,
  Calendar,
  Lock,
  CheckCircle2,
  ArrowRight,
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
  { id: 'Full-Service', title: 'Full-Service Royal Production', desc: 'End-to-end master planning, palace liaisons, royal hospitality, styling architecture, and artist management.' },
  { id: 'Partial-Concierge', title: 'Concierge & Production Direction', desc: 'Curated vendor management, celebration styling architecture, and flawless on-ground coordination.' },
  { id: 'Heritage-Venue', title: 'Venue & Royal Hospitality Management', desc: 'Dedicated focus on royal palace logistics, guest transfers, and ceremonial decor.' },
];

export const WebsiteRegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useClients();

  // Form State
  const [fullName, setFullName] = useState('');
  const [partnerName, setPartnerName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [weddingDate, setWeddingDate] = useState('');
  const [weddingLocation, setWeddingLocation] = useState('Udaipur Heritage Palace');
  const [expectedGuestCount, setExpectedGuestCount] = useState<number>(350);
  const [estimatedBudget, setEstimatedBudget] = useState<string>('25000000');
  const [selectedEvents, setSelectedEvents] = useState<string[]>([
    'Royal Sangeet & Musical Extravaganza',
    'Sacred Vedic Mandap & Pheras',
    'Grand Royal Reception Banquet'
  ]);
  const [preferredTheme, setPreferredTheme] = useState(THEME_OPTIONS[0]);
  const [servicePackage, setServicePackage] = useState('Full-Service');
  const [preferences, setPreferences] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [enquiryId, setEnquiryId] = useState<string>('');

  const toggleEvent = (eventTitle: string) => {
    setSelectedEvents(prev =>
      prev.includes(eventTitle) ? prev.filter(e => e !== eventTitle) : [...prev, eventTitle]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim() || !phone.trim() || !password.trim()) {
      setErrorMessage('Please complete all required fields.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters in length.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify your password entry.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        fullName: fullName.trim(),
        partnerName: partnerName.trim() || undefined,
        email: email.trim().toLowerCase(),
        password: password.trim(),
        phone: phone.trim(),
        weddingDate: weddingDate || undefined,
        weddingLocation: weddingLocation.trim() || undefined,
        expectedGuestCount: expectedGuestCount ? Number(expectedGuestCount) : undefined,
        estimatedBudget: estimatedBudget ? Number(estimatedBudget) : undefined,
        weddingEvents: selectedEvents,
        preferredTheme,
        servicePackage,
        preferences: preferences.trim() || undefined,
      };

      const res = await authApi.registerWebsite(payload);

      // Auto login client
      login(res.email, {
        name: res.client_name || fullName,
        role: 'Client'
      });

      setEnquiryId(res.enquiry_id || '');
      setIsSuccess(true);

      setTimeout(() => {
        navigate('/portal');
      }, 2500);

    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] text-[#1F2421] flex flex-col justify-center items-center p-6 selection:bg-[#9E7D3B] selection:text-white">
        <div className="max-w-lg w-full bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-12 text-center shadow-sm">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] mb-6">
            <CheckCircle2 size={24} />
          </div>

          <div className="text-[10px] tracking-[0.25em] uppercase text-[#9E7D3B] font-medium mb-2">
            The Royal Knot Concierge
          </div>
          <h1 className="font-serif text-3xl font-normal text-[#1F2421] mb-3">
            Celebration Dossier Registered
          </h1>

          <p className="text-xs text-[#736F68] leading-relaxed mb-6">
            Welcome, <strong>{fullName}</strong>. Your wedding celebration dossier has been successfully recorded in our central registry.
          </p>

          <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] mb-6 text-xs text-[#1F2421]">
            <div className="text-[10px] uppercase tracking-wider text-[#8C877D] mb-1">Your Enquiry Reference</div>
            <div className="font-mono text-base font-semibold text-[#9E7D3B]">{enquiryId}</div>
            <div className="text-[11px] text-[#736F68] mt-1">
              A formal confirmation has also been dispatched to <strong>{email}</strong>.
            </div>
          </div>

          <div className="text-xs text-[#9E7D3B] animate-pulse mb-6">
            Redirecting to your private client celebration portal...
          </div>

          <Link
            to="/portal"
            className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-6 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-medium hover:bg-[#9E7D3B] transition-colors"
          >
            <span>Enter Client Portal</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#1F2421] py-12 px-4 sm:px-6 selection:bg-[#9E7D3B] selection:text-white">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Brand Crest Header */}
        <div className="text-center space-y-2 pb-6 border-b border-[#E5E0D8]">
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium mb-1">
            <Sparkles size={14} />
            <span>Client Website Registration</span>
            <Sparkles size={14} />
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl text-[#1F2421] uppercase tracking-wider">
            The Royal Knot
          </h1>
          <p className="text-xs text-[#736F68] max-w-lg mx-auto">
            Create your client account and register your wedding celebration parameters with our luxury destination planning directors.
          </p>
        </div>

        {errorMessage && (
          <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs leading-relaxed">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8 bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-10 shadow-sm">
          {/* Section 1: Account Credentials */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
              <Lock size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-lg text-[#1F2421]">1. Account Credentials & Contact</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Your Full Name <span className="text-[#9E7D3B]">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Princess Gayatri Rao"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Partner's Full Name
                </label>
                <input
                  type="text"
                  value={partnerName}
                  onChange={(e) => setPartnerName(e.target.value)}
                  placeholder="e.g. Yuvraj Vikramaditya Singh"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Email Address (Login Username) <span className="text-[#9E7D3B]">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="client@royalknot.in"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Primary Phone / WhatsApp <span className="text-[#9E7D3B]">*</span>
                </label>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98200 11223"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Portal Password (min 8 chars) <span className="text-[#9E7D3B]">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Confirm Password <span className="text-[#9E7D3B]">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Celebration Parameters */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
              <Calendar size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-lg text-[#1F2421]">2. Celebration Date, Venue & Budget</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Target Celebration Date
                </label>
                <input
                  type="date"
                  value={weddingDate}
                  onChange={(e) => setWeddingDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Preferred Palace / Destination
                </label>
                <select
                  value={weddingLocation}
                  onChange={(e) => setWeddingLocation(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                >
                  <option value="Rambagh Palace, Jaipur">Rambagh Palace, Jaipur</option>
                  <option value="City Palace & Manek Chowk, Udaipur">City Palace & Manek Chowk, Udaipur</option>
                  <option value="Taj Lake Palace, Udaipur">Taj Lake Palace, Udaipur</option>
                  <option value="Umaid Bhawan Palace, Jodhpur">Umaid Bhawan Palace, Jodhpur</option>
                  <option value="The Leela Palace, Lake Pichola">The Leela Palace, Lake Pichola</option>
                  <option value="Samode Palace, Rajasthan">Samode Palace, Rajasthan</option>
                  <option value="Other Regal Heritage Destination">Other Regal Heritage Destination</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Expected Royal Guest Count
                </label>
                <input
                  type="number"
                  min="20"
                  max="2500"
                  value={expectedGuestCount}
                  onChange={(e) => setExpectedGuestCount(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
              </div>

              <div>
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                  Estimated Celebration Budget (₹)
                </label>
                <input
                  type="number"
                  step="500000"
                  value={estimatedBudget}
                  onChange={(e) => setEstimatedBudget(e.target.value)}
                  placeholder="25000000"
                  className="w-full px-3.5 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
                />
                <span className="text-[10px] text-[#9E7D3B] mt-1 block">
                  Approx: ₹ {(Number(estimatedBudget) / 10000000).toFixed(2)} Crores
                </span>
              </div>
            </div>
          </div>

          {/* Section 3: Ceremonies & Package Tier */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
              <Sparkles size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-lg text-[#1F2421]">3. Ceremonial Events & Service Tier</h2>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-2">
                Requested Ceremonies & Functions
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {EVENT_OPTIONS.map((ev) => (
                  <label
                    key={ev}
                    className={`flex items-center gap-2.5 p-3 border cursor-pointer transition-colors ${
                      selectedEvents.includes(ev)
                        ? 'bg-[#FAF8F5] border-[#9E7D3B] text-[#1F2421]'
                        : 'bg-white border-[#E5E0D8] text-[#736F68] hover:border-[#C5BFB5]'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(ev)}
                      onChange={() => toggleEvent(ev)}
                      className="accent-[#9E7D3B]"
                    />
                    <span>{ev}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-2">
                Retainer Package Tier
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {PACKAGE_OPTIONS.map((pkg) => (
                  <div
                    key={pkg.id}
                    onClick={() => setServicePackage(pkg.id)}
                    className={`p-3.5 border cursor-pointer transition-colors ${
                      servicePackage === pkg.id
                        ? 'bg-[#FAF8F5] border-[#9E7D3B] shadow-sm'
                        : 'bg-white border-[#E5E0D8] hover:border-[#C5BFB5]'
                    }`}
                  >
                    <div className="font-serif text-xs font-semibold text-[#1F2421] mb-1">{pkg.title}</div>
                    <div className="text-[10px] text-[#736F68] leading-relaxed">{pkg.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Preferred Aesthetic & Theme
              </label>
              <select
                value={preferredTheme}
                onChange={(e) => setPreferredTheme(e.target.value)}
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              >
                {THEME_OPTIONS.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Special Requests & Vision Notes
              </label>
              <textarea
                rows={3}
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
                placeholder="Mention any heritage palace preferences, vintage car processions, musical performers, or dietary traditions..."
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-6 border-t border-[#E5E0D8] flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-[11px] text-[#736F68]">
              Already have an account?{' '}
              <Link to="/login" className="text-[#9E7D3B] hover:underline font-medium">
                Sign in to Client Portal
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto px-8 py-3.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-semibold hover:bg-[#9E7D3B] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <span>{isSubmitting ? 'Registering Celebration...' : 'Create Account & Register Wedding'}</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
