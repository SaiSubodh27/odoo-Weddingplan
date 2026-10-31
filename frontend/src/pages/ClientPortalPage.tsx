import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Clock,
  CheckCircle2,
  LogOut,
  Building,
} from 'lucide-react';

export const ClientPortalPage: React.FC = () => {
  const { currentUser, logout } = useClients();
  const navigate = useNavigate();

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

          <div className="flex items-center gap-4 text-xs">
            <div className="hidden sm:block text-right">
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
              <span className="px-3 py-1 bg-[#F0F4FA] text-[#1D4E89] border border-[#B5CEEB] text-xs font-semibold uppercase tracking-wider">
                {dossier?.status ? dossier.status.replace('_', ' ') : 'Registration Submitted'}
              </span>
              {dossier?.enquiryId && (
                <span className="text-[11px] font-mono text-[#8C877D]">
                  Ref: <strong>{dossier.enquiryId}</strong>
                </span>
              )}
            </div>
          </div>
        </div>

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

          <div className="p-4 bg-white border border-[#E8D49E] bg-[#FDF6E2]/40">
            <div className="flex items-center gap-2 text-[#8C6D1F] text-xs font-semibold uppercase tracking-wider mb-1">
              <Clock size={14} />
              <span>2. Concierge Review</span>
            </div>
            <p className="text-[11px] text-[#736F68]">
              Senior wedding directors are reviewing palace availability and guest logistics.
            </p>
          </div>

          <div className="p-4 bg-white border border-[#E5E0D8]">
            <div className="flex items-center gap-2 text-[#8C877D] text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles size={14} />
              <span>3. Master Blueprint Consultation</span>
            </div>
            <p className="text-[11px] text-[#8C877D]">
              Formal presentation of ceremonial decor, artist lineups, and luxury hospitality.
            </p>
          </div>
        </div>

        {/* Detailed Celebration Parameters */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Parameters Card */}
            <div className="bg-white border border-[#E5E0D8] p-6 space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
                <Calendar size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-lg text-[#1F2421]">Registered Celebration Logistics</h2>
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

          {/* Right Column: Concierge Team Card */}
          <div className="space-y-6">
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
      </main>
    </div>
  );
};
