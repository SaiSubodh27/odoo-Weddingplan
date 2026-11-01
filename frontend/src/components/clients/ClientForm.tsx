import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../../context/ClientContext';
import { ServicePackage, EnquirySource, RegistrationStatus } from '../../types/client';
import { CheckCircle2, AlertCircle, ArrowLeft, Heart, Calendar, Building2, Sparkles, FileText } from 'lucide-react';

export const ClientForm: React.FC = () => {
  const navigate = useNavigate();
  const { addClient } = useClients();

  // Form State
  const [partner1Name, setPartner1Name] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const [weddingDate, setWeddingDate] = useState('');
  const [weddingLocation, setWeddingLocation] = useState('The Leela Palace, Udaipur');
  const [expectedGuestCount, setExpectedGuestCount] = useState<number>(300);
  const [estimatedBudget, setEstimatedBudget] = useState('₹ 1.50 Cr');
  const [weddingTheme, setWeddingTheme] = useState('Royal Rajputana Heritage and Floating Candles');

  const [servicePackage, setServicePackage] = useState<ServicePackage>('Full-Service');
  const [additionalRequirements, setAdditionalRequirements] = useState('');

  const [enquirySource, setEnquirySource] = useState<EnquirySource>('Website');
  const [status, setStatus] = useState<RegistrationStatus>('Enquiry');
  const [notes, setNotes] = useState('');

  // Validation & feedback state
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!partner1Name.trim()) newErrors.partner1Name = 'Partner 1 name is required';
    if (!partner2Name.trim()) newErrors.partner2Name = 'Partner 2 name is required';
    if (!email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please provide a valid email format';
    }
    if (!phone.trim()) newErrors.phone = 'Contact phone number is required';
    if (!weddingDate) newErrors.weddingDate = 'Wedding date is required';
    if (!weddingLocation.trim()) newErrors.weddingLocation = 'Wedding location/venue is required';
    if (!expectedGuestCount || expectedGuestCount <= 0) newErrors.expectedGuestCount = 'Valid guest count required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setIsSubmitting(true);

    const newId = addClient({
      partner1Name,
      partner2Name,
      email,
      phone,
      weddingDate,
      weddingLocation,
      expectedGuestCount: Number(expectedGuestCount),
      estimatedBudget,
      weddingTheme,
      servicePackage,
      additionalRequirements,
      enquirySource,
      notes,
      status
    });

    setSuccessMessage(`Client dossier successfully registered under Reference #${newId}`);

    // Wait briefly and navigate to clients page
    setTimeout(() => {
      navigate('/clients');
    }, 1200);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Success notification banner */}
      {successMessage && (
        <div className="p-4 bg-[#EBF3ED] border border-[#C3D9C9] flex items-center gap-3 text-[#2D5A3C]">
          <CheckCircle2 size={18} className="shrink-0" />
          <div className="text-xs font-semibold uppercase tracking-wider">{successMessage}</div>
        </div>
      )}

      {/* Validation warning */}
      {Object.keys(errors).length > 0 && (
        <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] flex items-center gap-3 text-[#94352D]">
          <AlertCircle size={18} className="shrink-0" />
          <div className="text-xs">
            Please correct the highlighted fields before saving the client record.
          </div>
        </div>
      )}

      {/* Section 1: Couple Details */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-[#E5E0D8]">
          <Heart size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">1. Couple Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Partner 1 Full Name *
            </label>
            <input
              type="text"
              value={partner1Name}
              onChange={(e) => setPartner1Name(e.target.value)}
              placeholder="e.g. Ananya Singhania"
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.partner1Name ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.partner1Name && <p className="text-[11px] text-red-600 mt-1">{errors.partner1Name}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Partner 2 Full Name *
            </label>
            <input
              type="text"
              value={partner2Name}
              onChange={(e) => setPartner2Name(e.target.value)}
              placeholder="e.g. Veer Rathore"
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.partner2Name ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.partner2Name && <p className="text-[11px] text-red-600 mt-1">{errors.partner2Name}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Primary Email Address *
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. couple@luxuryweddings.in"
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.email ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.email && <p className="text-[11px] text-red-600 mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Contact Phone / WhatsApp *
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

      {/* Section 2: Wedding Details */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-[#E5E0D8]">
          <Calendar size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">2. Destination Wedding Details</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Target Wedding Date *
            </label>
            <input
              type="date"
              value={weddingDate}
              onChange={(e) => setWeddingDate(e.target.value)}
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.weddingDate ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.weddingDate && <p className="text-[11px] text-red-600 mt-1">{errors.weddingDate}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Venue and Location *
            </label>
            <input
              type="text"
              value={weddingLocation}
              onChange={(e) => setWeddingLocation(e.target.value)}
              placeholder="e.g. Rambagh Palace, Jaipur"
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.weddingLocation ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.weddingLocation && <p className="text-[11px] text-red-600 mt-1">{errors.weddingLocation}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Expected Guest Count *
            </label>
            <input
              type="number"
              min="20"
              max="5000"
              value={expectedGuestCount}
              onChange={(e) => setExpectedGuestCount(Number(e.target.value))}
              className={`w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border text-[#1F2421] focus:outline-none focus:border-[#1F2421] ${
                errors.expectedGuestCount ? 'border-red-400 bg-red-50/20' : 'border-[#E5E0D8]'
              }`}
            />
            {errors.expectedGuestCount && <p className="text-[11px] text-red-600 mt-1">{errors.expectedGuestCount}</p>}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Estimated Budget
            </label>
            <input
              type="text"
              value={estimatedBudget}
              onChange={(e) => setEstimatedBudget(e.target.value)}
              placeholder="e.g. ₹ 1.50 Cr or ₹ 80 Lakhs"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Wedding Theme and Aesthetic Vision
            </label>
            <input
              type="text"
              value={weddingTheme}
              onChange={(e) => setWeddingTheme(e.target.value)}
              placeholder="e.g. Royal Marwar Heritage with Floating Jasmine and Lantern Courtyards"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>
        </div>
      </div>

      {/* Section 3: Service Scope */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-[#E5E0D8]">
          <Building2 size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">3. Service Engagement and Requirements</h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-2">
              Select Service Package
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  id: 'Full-Service',
                  title: 'Full-Service Royal Concierge',
                  desc: 'Comprehensive end-to-end planning, royal venue buyout, vendor curation and hospitality management.'
                },
                {
                  id: 'Partial-Service',
                  title: 'Partial-Service Planning',
                  desc: 'Decor design, artist management, and vendor negotiations with existing venue booking.'
                },
                {
                  id: 'Day-of Coordination',
                  title: 'Executive Day-of Coordination',
                  desc: 'On-site execution, timing choreography, VIP guest escorting, and seamless ceremony run-sheets.'
                }
              ].map((pkg) => (
                <div
                  key={pkg.id}
                  onClick={() => setServicePackage(pkg.id as ServicePackage)}
                  className={`p-4 border cursor-pointer transition-colors ${
                    servicePackage === pkg.id
                      ? 'border-[#1F2421] bg-[#FAF8F5]'
                      : 'border-[#E5E0D8] hover:border-[#8C877D] bg-[#FFFFFF]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-serif text-sm font-semibold text-[#1F2421]">{pkg.title}</span>
                    <span className={`w-3.5 h-3.5 border flex items-center justify-center ${
                      servicePackage === pkg.id ? 'border-[#1F2421] bg-[#1F2421]' : 'border-[#D9D3C7]'
                    }`}>
                      {servicePackage === pkg.id && <span className="w-1.5 h-1.5 bg-[#FFFFFF]" />}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#736F68] leading-relaxed">{pkg.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Additional Requirements and Special Requests
            </label>
            <textarea
              rows={3}
              value={additionalRequirements}
              onChange={(e) => setAdditionalRequirements(e.target.value)}
              placeholder="e.g. Royal boat arrival on Lake Pichola, private helicopter landing permissions, Michelin guest chefs, custom silver souvenir boxes..."
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>
        </div>
      </div>

      {/* Section 4: Registration & Status */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-[#E5E0D8]">
          <FileText size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">4. Registration and Internal Notes</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Enquiry Source
            </label>
            <select
              value={enquirySource}
              onChange={(e) => setEnquirySource(e.target.value as EnquirySource)}
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            >
              <option value="Website">Official Website</option>
              <option value="Email">Direct Inbound Email</option>
              <option value="Phone">VIP Phone Call</option>
              <option value="Luxury Concierge">Luxury Concierge Desk</option>
              <option value="Referral">Private Palace / Past Client Referral</option>
            </select>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Initial Registration Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as RegistrationStatus)}
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            >
              <option value="Enquiry">Enquiry</option>
              <option value="Registration Pending">Registration Pending</option>
              <option value="Registered">Registered</option>
              <option value="Agreement Pending">Agreement Pending</option>
              <option value="Confirmed">Confirmed</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Internal Planner Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Confidential remarks, family preferences, preferred astrologer dates, decision-makers..."
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>
        </div>
      </div>

      {/* Form Action Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-6 bg-[#FFFFFF] border border-[#E5E0D8]">
        <button
          type="button"
          onClick={() => navigate('/clients')}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 text-xs uppercase tracking-wider text-[#5C5850] bg-[#FAF8F5] border border-[#E5E0D8] hover:bg-[#F2EFE8] transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Cancel and Return</span>
        </button>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 text-xs uppercase tracking-wider font-semibold text-[#FAF8F5] bg-[#1F2421] hover:bg-[#343733] border border-[#1F2421] transition-colors disabled:opacity-50"
          >
            <Sparkles size={14} className="text-[#D9C496]" />
            <span>{isSubmitting ? 'Registering Client...' : 'Save and Register Client'}</span>
          </button>
        </div>
      </div>
    </form>
  );
};

