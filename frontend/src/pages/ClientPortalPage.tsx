import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import {
  Sparkles,
  Calendar,
  MapPin,
  Heart,
  Mail,
  Phone,
  Shield,
  CheckCircle2,
  LogOut,
  Building,
  FileText,
  ArrowRight,
  ClipboardList,
  Store
} from 'lucide-react';
import { ClientVendorCurator } from '../components/client/ClientVendorCurator';

export const ClientPortalPage: React.FC = () => {
  const { currentUser, logout, hasSignedAgreement } = useClients();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState<'blueprint' | 'vendors'>(
    tabParam === 'vendors' ? 'vendors' : 'blueprint'
  );

  const [dossier, setDossier] = useState<any | null>(null);

  useEffect(() => {
    async function loadDossier() {
      if (!currentUser.email) return;
      try {
        const data = await authApi.getClientDossier(currentUser.email);
        setDossier(data);
      } catch (err) {
        console.error('Failed to load dossier:', err);
      }
    }
    loadDossier();
  }, [currentUser.email]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleTabChange = (tab: 'blueprint' | 'vendors') => {
    setActiveTab(tab);
    setSearchParams(tab === 'vendors' ? { tab: 'vendors' } : {});
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#1F2421] selection:bg-[#9E7D3B] selection:text-white">
      {/* Top Luxury Client Navbar */}
      <header className="bg-[#FFFFFF] border-b border-[#E5E0D8] px-6 py-4 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#FAF8F5] border border-[#E5E0D8] flex items-center justify-center text-[#9E7D3B]">
              <Sparkles size={16} />
            </div>
            <div>
              <div className="font-serif text-lg text-[#1F2421] uppercase tracking-wider">
                The Royal Knot
              </div>
              <div className="text-[9px] uppercase tracking-[0.25em] text-[#9E7D3B] font-medium">
                Client Celebration Portal
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 text-xs">
            {/* Quick Vendor Tab Button */}
            <button
              onClick={() => handleTabChange(activeTab === 'vendors' ? 'blueprint' : 'vendors')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border transition-colors ${
                activeTab === 'vendors'
                  ? 'bg-[#1F2421] text-white border-[#1F2421] font-semibold'
                  : 'text-[#9E7D3B] hover:text-[#1F2421] border-[#9E7D3B]/40 bg-[#FAF8F5] hover:bg-white font-medium'
              }`}
            >
              <Store size={13} />
              <span>{activeTab === 'vendors' ? 'Celebration Blueprint' : 'Curate Vendors & Budget'}</span>
            </button>

            {/* Quick Navigation Links */}
            <Link
              to="/agreement"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#9E7D3B] hover:text-[#1F2421] border border-[#E5E0D8] bg-[#FAF8F5] hover:bg-white transition-colors"
            >
              <FileText size={13} />
              <span>Service Agreement</span>
            </Link>

            <Link
              to="/client-intake"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#736F68] hover:text-[#1F2421] border border-[#E5E0D8] bg-[#FAF8F5] hover:bg-white transition-colors"
            >
              <ClipboardList size={13} />
              <span>Celebration Details</span>
            </Link>

            <div className="hidden md:block text-right border-l border-[#E5E0D8] pl-4">
              <div className="font-medium text-[#1F2421]">{currentUser.name || 'Private Client'}</div>
              <div className="text-[10px] text-[#8C877D]">{currentUser.email}</div>
            </div>

            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#736F68] hover:text-[#94352D] border border-[#E5E0D8] bg-[#FAF8F5] hover:bg-white transition-colors"
            >
              <LogOut size={13} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
        {/* Welcome Hero Banner */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 relative overflow-hidden shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
                <Heart size={12} />
                <span>Private Celebration Dossier</span>
              </div>
              <h1 className="font-serif text-2xl sm:text-3xl text-[#1F2421]">
                {dossier?.fullName || currentUser.name} {dossier?.partnerName ? `& ${dossier.partnerName}` : ''}
              </h1>
              <p className="text-xs text-[#736F68] max-w-xl">
                Welcome to your bespoke wedding management portal. Your assigned wedding directors in Jaipur and Udaipur are preparing your celebration blueprint.
              </p>
            </div>

            <div className="flex flex-col items-start md:items-end gap-2 shrink-0">
              <span className="text-[10px] uppercase tracking-wider text-[#8C877D]">Dossier Status</span>
              <span className="px-3 py-1 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] text-xs font-semibold uppercase tracking-wider">
                {dossier?.status ? dossier.status.replace('_', ' ') : 'Confirmed'}
              </span>
              {dossier?.enquiryId && (
                <span className="text-[11px] font-mono text-[#8C877D]">
                  Ref: <strong>{dossier.enquiryId}</strong>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation System */}
        <div className="flex border-b border-[#E5E0D8] bg-white px-6 pt-3 shadow-sm">
          <button
            type="button"
            onClick={() => handleTabChange('blueprint')}
            className={`pb-3 px-4 text-xs font-semibold uppercase tracking-wider flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'blueprint'
                ? 'border-[#9E7D3B] text-[#9E7D3B]'
                : 'border-transparent text-[#736F68] hover:text-[#1F2421]'
            }`}
          >
            <Calendar size={14} />
            <span>Celebration Blueprint & Logistics</span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange('vendors')}
            className={`pb-3 px-4 text-xs font-semibold uppercase tracking-wider flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'vendors'
                ? 'border-[#9E7D3B] text-[#9E7D3B]'
                : 'border-transparent text-[#736F68] hover:text-[#1F2421]'
            }`}
          >
            <Store size={14} />
            <span>Curate Royal Vendors & Budget</span>
            <span className="px-1.5 py-0.5 text-[9px] bg-[#9E7D3B] text-white font-mono font-bold rounded">
              Interactive
            </span>
          </button>
        </div>

        {/* TAB 1: BLUEPRINT VIEW */}
        {activeTab === 'blueprint' && (
          <div className="space-y-6 animate-fadeIn">
            {/* Milestone Steps */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 bg-white border border-[#C3D9C9] bg-[#EBF3ED]/30">
                <div className="flex items-center gap-2 text-[#2D5A3C] text-xs font-semibold uppercase tracking-wider mb-1">
                  <CheckCircle2 size={14} />
                  <span>1. Registration Dossier</span>
                </div>
                <p className="text-[11px] text-[#736F68]">
                  Celebration parameters and palace venue preferences successfully recorded.
                </p>
              </div>

              <div className="p-4 bg-white border border-[#C3D9C9] bg-[#EBF3ED]/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[#2D5A3C] text-xs font-semibold uppercase tracking-wider mb-1">
                    <CheckCircle2 size={14} />
                    <span>2. Service Agreement</span>
                  </div>
                  <Link to="/agreement" className="text-[10px] text-[#9E7D3B] hover:underline flex items-center gap-0.5">
                    View <ArrowRight size={10} />
                  </Link>
                </div>
                <p className="text-[11px] text-[#736F68]">
                  {hasSignedAgreement 
                    ? 'Legally executed & digitally ratified by client.' 
                    : 'Service agreement ratified with 18% GST and payment schedule.'}
                </p>
              </div>

              <div 
                onClick={() => handleTabChange('vendors')}
                className="p-4 bg-white border border-[#E8D49E] bg-[#FDF6E2]/40 cursor-pointer hover:border-[#9E7D3B] transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2 text-[#8C6D1F] text-xs font-semibold uppercase tracking-wider">
                    <Store size={14} />
                    <span>3. Choose Vendors & Budget</span>
                  </div>
                  <span className="text-[10px] text-[#9E7D3B] group-hover:underline flex items-center gap-0.5">
                    Curate <ArrowRight size={10} />
                  </span>
                </div>
                <p className="text-[11px] text-[#736F68]">
                  Select verified palace caterers, florists, photography & baraat teams within your budget.
                </p>
              </div>
            </div>

            {/* Detailed Celebration Parameters */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Parameters Card */}
                <div className="bg-white border border-[#E5E0D8] p-6 space-y-6">
                  <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
                    <div className="flex items-center gap-2">
                      <Calendar size={16} className="text-[#9E7D3B]" />
                      <h2 className="font-serif text-lg text-[#1F2421]">Registered Celebration Logistics</h2>
                    </div>
                    <Link
                      to="/client-intake"
                      className="text-xs text-[#9E7D3B] hover:underline font-medium flex items-center gap-1"
                    >
                      Edit Logistics <ArrowRight size={12} />
                    </Link>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                        Target Celebration Date
                      </span>
                      <div className="font-semibold text-[#1F2421] text-sm">
                        {dossier?.weddingDate ? new Date(dossier.weddingDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : 'To be finalized'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                        Destination Palace Venue
                      </span>
                      <div className="font-semibold text-[#1F2421] text-sm">
                        {dossier?.weddingLocation || 'Rajasthan Heritage Palace'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                        Expected Royal Guest Count
                      </span>
                      <div className="font-semibold text-[#1F2421] text-sm">
                        {dossier?.expectedGuestCount ? `${dossier.expectedGuestCount} Guests` : 'Approx. 350 Guests'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                        Estimated Celebration Budget
                      </span>
                      <div className="font-semibold text-[#1F2421] text-sm">
                        {dossier?.estimatedBudget ? `₹ ${(dossier.estimatedBudget / 10000000).toFixed(2)} Crores` : '₹ 2.50 Crores'}
                      </div>
                    </div>
                  </div>

                  {/* Ceremonies List */}
                  <div className="pt-4 border-t border-[#E5E0D8]">
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-2">
                      Requested Ceremonies & Functions
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {dossier?.weddingEvents && dossier.weddingEvents.length > 0 ? (
                        dossier.weddingEvents.map((ev: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#1F2421]"
                          >
                            {ev}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-[#736F68]">
                          Royal Sangeet, Vedic Mandap & Pheras, Grand Reception Banquet
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Aesthetic & Theme */}
                  <div className="pt-4 border-t border-[#E5E0D8] text-xs">
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                      Preferred Theme & Retainer Tier
                    </span>
                    <div className="text-[#1F2421] font-medium">
                      {dossier?.preferredTheme || 'Regal Rajputana Heritage & Floating Palace Splendor'}
                    </div>
                    <div className="text-[11px] text-[#9E7D3B] mt-0.5 font-semibold">
                      Package: {dossier?.servicePackage || 'Full-Service Royal Production'}
                    </div>
                  </div>

                  {/* Notes */}
                  {dossier?.preferences && (
                    <div className="pt-4 border-t border-[#E5E0D8] text-xs">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                        Special Wishes & Requirements
                      </span>
                      <p className="bg-[#FAF8F5] p-3 border border-[#E5E0D8] text-[#1F2421] leading-relaxed">
                        {dossier.preferences}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Vendor Callout & Agreement Access */}
              <div className="space-y-6">
                {/* Vendor Curator Callout Card */}
                <div className="bg-gradient-to-br from-[#1F2421] to-[#2A312B] text-white p-6 space-y-4 shadow-sm border border-[#3E453F]">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#4A524B]">
                    <Store size={16} className="text-[#D9C496]" />
                    <h3 className="font-serif text-base text-white">Choose Your Palace Vendors</h3>
                  </div>

                  <p className="text-xs text-[#C5BFA9] leading-relaxed">
                    Select catering, decor, photography, and entertainment vendors directly tailored to your celebration budget.
                  </p>

                  <button
                    type="button"
                    onClick={() => handleTabChange('vendors')}
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#9E7D3B] text-white text-xs uppercase tracking-wider font-semibold hover:bg-[#8A6C32] transition-colors shadow-sm"
                  >
                    <span>Open Vendor Curator</span>
                    <ArrowRight size={13} />
                  </button>
                </div>

                <div className="bg-white border border-[#E5E0D8] p-6 space-y-4">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
                    <FileText size={16} className="text-[#9E7D3B]" />
                    <h3 className="font-serif text-base text-[#1F2421]">Service Agreement</h3>
                  </div>

                  <p className="text-xs text-[#736F68] leading-relaxed">
                    Your legally binding service agreement outlining milestone disbursements, GST invoice schedules, and cancellation covenants.
                  </p>

                  <Link
                    to="/agreement"
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-medium hover:bg-[#343733] transition-colors"
                  >
                    <span>Review Service Agreement</span>
                    <ArrowRight size={13} className="text-[#D9C496]" />
                  </Link>
                </div>

                <div className="bg-white border border-[#E5E0D8] p-6 space-y-4">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
                    <Building size={16} className="text-[#9E7D3B]" />
                    <h3 className="font-serif text-base text-[#1F2421]">Dedicated Concierge Desk</h3>
                  </div>

                  <p className="text-xs text-[#736F68] leading-relaxed">
                    Your dossier has been routed to our Senior Rajasthan Concierge Directors. For urgent requirements or private palace viewing arrangements, contact:
                  </p>

                  <div className="space-y-2.5 text-xs">
                    <div className="flex items-center gap-2 text-[#1F2421]">
                      <Mail size={13} className="text-[#9E7D3B]" />
                      <span>saisubodh6@gmail.com</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#1F2421]">
                      <Phone size={13} className="text-[#9E7D3B]" />
                      <span>+91 98290 88888</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#736F68] text-[11px]">
                      <MapPin size={13} className="text-[#9E7D3B]" />
                      <span>Jaipur: Rambagh Enclave · Udaipur: Lake Pichola</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-5 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-[#1F2421]">
                    <Shield size={14} className="text-[#9E7D3B]" />
                    <span>Confidential Client Portal</span>
                  </div>
                  <p className="text-[11px] text-[#736F68] leading-relaxed">
                    All guest parameters, royal venue negotiations, and celebration contracts are encrypted under The Royal Knot Privacy Protocol.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: VENDOR CURATION VIEW */}
        {activeTab === 'vendors' && (
          <div className="animate-fadeIn">
            <ClientVendorCurator
              clientEmail={currentUser.email || 'aarav.meera@heritage-singhania.com'}
              initialBudget={dossier?.estimatedBudget || 25000000}
              weddingLocation={dossier?.weddingLocation || 'Rajasthan Heritage Palace'}
              guestCount={dossier?.expectedGuestCount || 350}
            />
          </div>
        )}
      </main>
    </div>
  );
};
