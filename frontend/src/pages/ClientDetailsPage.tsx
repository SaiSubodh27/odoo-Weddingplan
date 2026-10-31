import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { RegistrationStatus } from '../types/client';
import { getStatusBadgeStyle } from '../components/clients/ClientTable';
import { 
  ArrowLeft, 
  Heart, 
  Calendar, 
  MapPin, 
  Mail, 
  Phone, 
  Building2, 
  FileText, 
  Clock, 
  Users, 
  Banknote,
  FileCheck,
  UtensilsCrossed,
  Store,
  CreditCard,
  Lock,
  Printer,
  Sparkles
} from 'lucide-react';

export const ClientDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getClient, updateClientStatus } = useClients();

  const client = getClient(id || '');
  const [selectedStatus, setSelectedStatus] = useState<RegistrationStatus>(
    client?.status || 'Enquiry'
  );
  const [statusUpdateMessage, setStatusUpdateMessage] = useState<string | null>(null);

  if (!client) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center max-w-xl mx-auto space-y-4">
        <h2 className="font-serif text-2xl text-[#1F2421]">Client Record Not Found</h2>
        <p className="text-xs text-[#736F68]">
          The client reference ID "{id}" could not be located in the current system records.
        </p>
        <Link
          to="/clients"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
        >
          <ArrowLeft size={14} />
          <span>Back to Directory</span>
        </Link>
      </div>
    );
  }

  const handleStatusChange = (newStatus: RegistrationStatus) => {
    setSelectedStatus(newStatus);
    updateClientStatus(client.id, newStatus);
    setStatusUpdateMessage(`Status updated to ${newStatus}`);
    setTimeout(() => setStatusUpdateMessage(null), 3000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top back navigation & quick actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/clients')}
            className="p-2 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] text-[#1F2421]"
            title="Back to Clients"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
              <span>Client Dossier</span>
              <span>·</span>
              <span>Ref: {client.id}</span>
            </div>
            <h1 className="font-serif text-3xl text-[#1F2421]">
              {client.partner1Name} & {client.partner2Name}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status badge & selector */}
          <div className="flex items-center gap-2 border border-[#E5E0D8] bg-[#FFFFFF] px-3 py-1.5">
            <span className="text-[10px] uppercase tracking-wider text-[#736F68]">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => handleStatusChange(e.target.value as RegistrationStatus)}
              className="text-xs font-semibold bg-transparent border-none text-[#1F2421] focus:ring-0 cursor-pointer"
            >
              <option value="Enquiry">Enquiry</option>
              <option value="Registration Pending">Registration Pending</option>
              <option value="Registered">Registered</option>
              <option value="Agreement Pending">Agreement Pending</option>
              <option value="Confirmed">Confirmed</option>
            </select>
          </div>

          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-3 py-2 bg-[#FFFFFF] hover:bg-[#FAF8F5] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#1F2421] transition-colors"
          >
            <Printer size={14} className="text-[#9E7D3B]" />
            <span>Print Dossier</span>
          </button>
        </div>
      </div>

      {statusUpdateMessage && (
        <div className="p-3 bg-[#EBF3ED] border border-[#C3D9C9] text-xs font-semibold text-[#2D5A3C] uppercase tracking-wider">
          {statusUpdateMessage}
        </div>
      )}

      {/* Main Info Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (2 Cols): Wedding & Service Specs */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Wedding Specs Box */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8] mb-6">
              <Sparkles size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Palace Destination Wedding Overview</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                  Chosen Venue & Destination
                </span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <MapPin size={14} className="text-[#9E7D3B]" />
                  <span>{client.weddingLocation}</span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                  Wedding Date
                </span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <Calendar size={14} className="text-[#9E7D3B]" />
                  <span>
                    {new Date(client.weddingDate).toLocaleDateString('en-IN', {
                      weekday: 'long',
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                  Expected Royal Guests
                </span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <Users size={14} className="text-[#9E7D3B]" />
                  <span>{client.expectedGuestCount} Guests</span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                  Estimated Agency Budget
                </span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <Banknote size={14} className="text-[#9E7D3B]" />
                  <span>{client.estimatedBudget}</span>
                </div>
              </div>

              <div className="sm:col-span-2 space-y-1 pt-2 border-t border-[#E5E0D8]/60">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                  Design Aesthetic & Theme
                </span>
                <p className="text-xs text-[#1F2421] font-medium bg-[#FAF8F5] p-3 border border-[#E5E0D8]">
                  "{client.weddingTheme}"
                </p>
              </div>
            </div>
          </div>

          {/* Service Package & Additional Requirements */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8] mb-6">
              <Building2 size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Service Package & Scope</h2>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block mb-1">
                  Selected Package Tier
                </span>
                <div className="inline-block px-3 py-1.5 bg-[#FAF8F5] border border-[#1F2421] font-semibold text-[#1F2421]">
                  {client.servicePackage}
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block mb-1">
                  Bespoke Requirements & Special Additions
                </span>
                <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] leading-relaxed">
                  {client.additionalRequirements || 'No specific additions noted during initial consultation.'}
                </div>
              </div>
            </div>
          </div>

          {/* Internal Notes */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8] mb-4">
              <FileText size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Confidential Planner Notes</h2>
            </div>
            <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#5C5850] leading-relaxed">
              {client.notes || 'No confidential notes recorded yet.'}
            </div>
          </div>

        </div>

        {/* Right Column (1 Col): Couple Contact & Registration Meta */}
        <div className="space-y-6">
          
          {/* Couple Contact Card */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8] mb-4">
              <Heart size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Couple Contacts</h2>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Partner 1</span>
                <div className="text-sm font-semibold text-[#1F2421]">{client.partner1Name}</div>
              </div>

              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Partner 2</span>
                <div className="text-sm font-semibold text-[#1F2421]">{client.partner2Name}</div>
              </div>

              <div className="pt-2 border-t border-[#E5E0D8]">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Email Address</span>
                <a
                  href={`mailto:${client.email}`}
                  className="flex items-center gap-1.5 text-[#1F2421] hover:text-[#9E7D3B] font-medium"
                >
                  <Mail size={13} className="text-[#9E7D3B]" />
                  <span>{client.email}</span>
                </a>
              </div>

              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Telephone / WhatsApp</span>
                <a
                  href={`tel:${client.phone}`}
                  className="flex items-center gap-1.5 text-[#1F2421] hover:text-[#9E7D3B] font-medium"
                >
                  <Phone size={13} className="text-[#9E7D3B]" />
                  <span>{client.phone}</span>
                </a>
              </div>
            </div>
          </div>

          {/* Registration Metadata */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8] mb-4">
              <Clock size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Dossier Meta</h2>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-[#E5E0D8]/60">
                <span className="text-[#8C877D]">Reference ID</span>
                <span className="font-mono font-medium text-[#1F2421]">{client.id}</span>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-[#E5E0D8]/60">
                <span className="text-[#8C877D]">Registration Date</span>
                <span className="text-[#1F2421]">{client.createdAt}</span>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-[#E5E0D8]/60">
                <span className="text-[#8C877D]">Enquiry Channel</span>
                <span className="text-[#1F2421]">{client.enquirySource}</span>
              </div>

              <div className="flex justify-between items-center py-1">
                <span className="text-[#8C877D]">Current Status</span>
                <span className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold border ${getStatusBadgeStyle(client.status)}`}>
                  {client.status}
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Future Modules Section (Coming Soon Placeholders) */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8">
        <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8] mb-6">
          <div>
            <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
              System Expansion Roadmap
            </div>
            <h2 className="font-serif text-2xl text-[#1F2421]">Upcoming Management Modules</h2>
          </div>
          <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider bg-[#FAF8F5] border border-[#E5E0D8] text-[#8C877D]">
            Phase 2 Modules
          </span>
        </div>

        <p className="text-xs text-[#736F68] mb-6 leading-relaxed">
          The following enterprise modules will integrate seamlessly with this client dossier once backend contracts and accounting engines are connected.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Module 1: Service Agreement */}
          <div className="p-5 border border-[#E5E0D8] bg-[#FAF8F5] opacity-75 relative group">
            <div className="flex items-center justify-between mb-3">
              <FileCheck size={20} className="text-[#9E7D3B]" />
              <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-[#8C877D] border border-[#E5E0D8] px-1.5 py-0.5 bg-[#FFFFFF]">
                <Lock size={10} />
                <span>Coming Soon</span>
              </span>
            </div>
            <h3 className="font-serif text-base font-semibold text-[#1F2421] mb-1">
              Service Agreement
            </h3>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Bespoke legal contracts, NDA covenants, payment schedules, and digital signatures.
            </p>
          </div>

          {/* Module 2: Catering Requirements */}
          <div className="p-5 border border-[#E5E0D8] bg-[#FAF8F5] opacity-75 relative group">
            <div className="flex items-center justify-between mb-3">
              <UtensilsCrossed size={20} className="text-[#9E7D3B]" />
              <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-[#8C877D] border border-[#E5E0D8] px-1.5 py-0.5 bg-[#FFFFFF]">
                <Lock size={10} />
                <span>Coming Soon</span>
              </span>
            </div>
            <h3 className="font-serif text-base font-semibold text-[#1F2421] mb-1">
              Catering Requirements
            </h3>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Royal Marwari degustation menus, live counter setups, wine pairings, and dietary logs.
            </p>
          </div>

          {/* Module 3: Vendor Quotations */}
          <div className="p-5 border border-[#E5E0D8] bg-[#FAF8F5] opacity-75 relative group">
            <div className="flex items-center justify-between mb-3">
              <Store size={20} className="text-[#9E7D3B]" />
              <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-[#8C877D] border border-[#E5E0D8] px-1.5 py-0.5 bg-[#FFFFFF]">
                <Lock size={10} />
                <span>Coming Soon</span>
              </span>
            </div>
            <h3 className="font-serif text-base font-semibold text-[#1F2421] mb-1">
              Vendor Quotations
            </h3>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Comparison grids for florists, sound/light technicians, vintage cars, and fireworks artisans.
            </p>
          </div>

          {/* Module 4: Payments & Settlements */}
          <div className="p-5 border border-[#E5E0D8] bg-[#FAF8F5] opacity-75 relative group">
            <div className="flex items-center justify-between mb-3">
              <CreditCard size={20} className="text-[#9E7D3B]" />
              <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-[#8C877D] border border-[#E5E0D8] px-1.5 py-0.5 bg-[#FFFFFF]">
                <Lock size={10} />
                <span>Coming Soon</span>
              </span>
            </div>
            <h3 className="font-serif text-base font-semibold text-[#1F2421] mb-1">
              Payments & Settlements
            </h3>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Milestone payment schedules, advance deposits, escrow disbursements, and GST invoicing.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
};

