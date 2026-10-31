import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { enquiryApi } from '../services/api';
import { EnquirySource } from '../types/enquiry';
import { 
  ArrowLeft, 
  Sparkles, 
  Mail, 
  Phone, 
  Calendar, 
  FileText,
  AlertCircle
} from 'lucide-react';

export const AddEnquiryPage: React.FC = () => {
  const navigate = useNavigate();

  const [clientName, setClientName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [enquirySource, setEnquirySource] = useState<EnquirySource>('Email');
  const [weddingDate, setWeddingDate] = useState('');
  const [weddingLocation, setWeddingLocation] = useState('Udaipur / Jaipur');
  const [expectedGuestCount, setExpectedGuestCount] = useState<number | ''>(300);
  const [estimatedBudget, setEstimatedBudget] = useState('₹ 1.50 Cr');
  const [requirements, setRequirements] = useState('');
  const [internalNotes, setInternalNotes] = useState('');

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!clientName.trim()) newErrors.clientName = 'Client/Couple name is required';
    if (!email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Valid email address required';
    }
    if (!phone.trim()) newErrors.phone = 'Phone/WhatsApp number is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        clientName,
        email,
        phone,
        enquirySource,
        weddingDate: weddingDate || null,
        weddingLocation: weddingLocation || null,
        expectedGuestCount: expectedGuestCount ? Number(expectedGuestCount) : null,
        estimatedBudget: estimatedBudget || null,
        requirements: requirements || null,
        internalNotes: internalNotes || null,
        status: 'New'
      };

      const created = await enquiryApi.create(payload);
      navigate(`/enquiries/${created.id}`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to record enquiry.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-6 border-b border-[#E5E0D8]">
        <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
          Inbound Reception Desk
        </div>
        <h1 className="font-serif text-3xl text-[#1F2421]">Record Inbound Enquiry</h1>
        <p className="text-xs text-[#736F68] mt-1">
          Log an incoming destination wedding inquiry received via Email or Phone call.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Source & Client Contact */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
            <Sparkles size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-xl text-[#1F2421]">1. Channel & Contact Person</h2>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-2">
              Inbound Enquiry Channel *
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setEnquirySource('Email')}
                className={`p-4 border flex items-center gap-3 transition-colors ${
                  enquirySource === 'Email'
                    ? 'border-[#1F2421] bg-[#FAF8F5]'
                    : 'border-[#E5E0D8] bg-[#FFFFFF] hover:border-[#8C877D]'
                }`}
              >
                <Mail size={18} className="text-[#9E7D3B]" />
                <div className="text-left">
                  <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">Email Inquiry</div>
                  <div className="text-[11px] text-[#736F68]">Received in concierge mailbox</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setEnquirySource('Phone')}
                className={`p-4 border flex items-center gap-3 transition-colors ${
                  enquirySource === 'Phone'
                    ? 'border-[#1F2421] bg-[#FAF8F5]'
                    : 'border-[#E5E0D8] bg-[#FFFFFF] hover:border-[#8C877D]'
                }`}
              >
                <Phone size={18} className="text-[#9E7D3B]" />
                <div className="text-left">
                  <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">Phone Call Inquiry</div>
                  <div className="text-[11px] text-[#736F68]">Direct verbal briefing</div>
                </div>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Client / Couple Name *
              </label>
              <input
                type="text"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="e.g. Princess Gayatri Rao"
                className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                  errors.clientName ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
                }`}
              />
              {errors.clientName && <p className="text-[11px] text-red-600 mt-1">{errors.clientName}</p>}
            </div>

            <div className="md:col-span-1">
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Client Email *
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="client@luxuryheritagedrive.com"
                className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                  errors.email ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
                }`}
              />
              {errors.email && <p className="text-[11px] text-red-600 mt-1">{errors.email}</p>}
            </div>

            <div className="md:col-span-1">
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Phone Number / WhatsApp *
              </label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98200 00000"
                className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                  errors.phone ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
                }`}
              />
              {errors.phone && <p className="text-[11px] text-red-600 mt-1">{errors.phone}</p>}
            </div>
          </div>
        </div>

        {/* Section 2: Wedding Parameters */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
            <Calendar size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-xl text-[#1F2421]">2. Target Celebration Scope</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Target Wedding Date
              </label>
              <input
                type="date"
                value={weddingDate}
                onChange={(e) => setWeddingDate(e.target.value)}
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Destination / Venue
              </label>
              <input
                type="text"
                value={weddingLocation}
                onChange={(e) => setWeddingLocation(e.target.value)}
                placeholder="e.g. City Palace, Udaipur"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Expected Guests
              </label>
              <input
                type="number"
                value={expectedGuestCount}
                onChange={(e) => setExpectedGuestCount(e.target.value ? Number(e.target.value) : '')}
                placeholder="350"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Estimated Budget
              </label>
              <input
                type="text"
                value={estimatedBudget}
                onChange={(e) => setEstimatedBudget(e.target.value)}
                placeholder="₹ 2.0 Cr"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div className="sm:col-span-2 lg:col-span-4">
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Client Requirements or Message
              </label>
              <textarea
                rows={3}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Details shared in the email or phone call (e.g. royal boat procession, vintage car transfers, heritage acoustic performances...)"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Internal Notes */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-4">
          <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
            <FileText size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-xl text-[#1F2421]">3. Confidential Staff Intake Notes</h2>
          </div>

          <div>
            <textarea
              rows={3}
              value={internalNotes}
              onChange={(e) => setInternalNotes(e.target.value)}
              placeholder="Initial remarks, caller relation (e.g. bride's father, VIP secretary), immediate follow-up actions..."
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between p-6 bg-[#FFFFFF] border border-[#E5E0D8]">
          <button
            type="button"
            onClick={() => navigate('/enquiries')}
            className="flex items-center gap-2 px-5 py-2.5 text-xs uppercase tracking-wider text-[#5C5850] bg-[#FAF8F5] border border-[#E5E0D8] hover:bg-[#F2EFE8]"
          >
            <ArrowLeft size={14} />
            <span>Cancel</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 px-8 py-3 text-xs uppercase tracking-wider font-semibold text-[#FAF8F5] bg-[#1F2421] hover:bg-[#343733] border border-[#1F2421] disabled:opacity-60"
          >
            <Sparkles size={14} className="text-[#D9C496]" />
            <span>{isSubmitting ? 'Recording Enquiry...' : 'Save Inbound Enquiry'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
