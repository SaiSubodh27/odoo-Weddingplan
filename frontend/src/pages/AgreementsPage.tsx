import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Plus, 
  Search, 
  Filter, 
  ArrowRight,
  ShieldCheck,
  Send,
  Calendar,
  Sparkles
} from 'lucide-react';
import { agreementApi } from '../services/api';
import { ServiceAgreement, AgreementMetrics } from '../types/agreement';

export const AgreementsPage: React.FC = () => {
  const navigate = useNavigate();
  const [agreements, setAgreements] = useState<ServiceAgreement[]>([]);
  const [metrics, setMetrics] = useState<AgreementMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  const fetchMetricsAndList = async () => {
    setLoading(true);
    try {
      const [m, res] = await Promise.all([
        agreementApi.getMetrics().catch(() => null),
        agreementApi.list({ search, status: statusFilter })
      ]);
      if (m) setMetrics(m);
      if (res && res.items) setAgreements(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsAndList();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchMetricsAndList();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'APPROVED_TO_SEND':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'SIGNING_PENDING':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'UNDER_VERIFICATION':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'VERIFIED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'BOOKING_CONFIRMED':
        return 'bg-[#1F2421] text-[#FAF8F5] border-[#1F2421]';
      case 'REJECTED':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div>
          <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
            Phase 2 · Contractual Operations
          </div>
          <h1 className="font-serif text-3xl text-[#1F2421]">Service Agreements & Booking Dossiers</h1>
          <p className="text-xs text-[#736F68] mt-1">
            Bespoke client contracts, ReportLab PDF generation, Zoho Sign invitations, and authorized booking confirmations.
          </p>
        </div>

        <button
          onClick={() => navigate('/agreements/new')}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#9E7D3B] hover:bg-[#86682F] text-white text-xs uppercase tracking-widest font-medium transition-colors shadow-sm"
        >
          <Plus size={14} />
          Create Agreement
        </button>
      </div>

      {/* Metrics Row */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white border border-[#E5E0D8] p-4 flex flex-col justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">Total Agreements</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="font-serif text-2xl font-bold text-[#1F2421]">{metrics.total_agreements}</span>
              <FileText size={16} className="text-[#9E7D3B]" />
            </div>
          </div>

          <div className="bg-white border border-[#E5E0D8] p-4 flex flex-col justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">Awaiting Signing</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="font-serif text-2xl font-bold text-purple-700">{metrics.signing_pending}</span>
              <Send size={16} className="text-purple-600" />
            </div>
          </div>

          <div className="bg-white border border-[#E5E0D8] p-4 flex flex-col justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">Awaiting Verification</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="font-serif text-2xl font-bold text-indigo-700">{metrics.awaiting_verification}</span>
              <ShieldCheck size={16} className="text-indigo-600" />
            </div>
          </div>

          <div className="bg-white border border-[#E5E0D8] p-4 flex flex-col justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">Confirmed Bookings</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="font-serif text-2xl font-bold text-emerald-800">{metrics.confirmed_bookings}</span>
              <Sparkles size={16} className="text-emerald-600" />
            </div>
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div className="bg-white border border-[#E5E0D8] p-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8C877D]" />
          <input
            type="text"
            placeholder="Search by Agreement No (e.g. RK-SA-2026-001) or Client Name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-[#E5E0D8] text-xs focus:outline-none focus:border-[#9E7D3B]"
          />
        </form>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-[#8C877D]" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-[#E5E0D8] text-xs py-2 px-3 focus:outline-none focus:border-[#9E7D3B] bg-white text-[#1F2421]"
          >
            <option value="All">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="APPROVED_TO_SEND">Approved to Send</option>
            <option value="SIGNING_PENDING">Signing Pending (Zoho Sign)</option>
            <option value="UNDER_VERIFICATION">Under Verification</option>
            <option value="VERIFIED">Verified</option>
            <option value="BOOKING_CONFIRMED">Booking Confirmed</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Agreement Table */}
      <div className="bg-white border border-[#E5E0D8] overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#8C877D]">Loading agreement dossiers...</div>
        ) : agreements.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#8C877D] space-y-3">
            <p>No service agreements matching the selected criteria.</p>
            <button
              onClick={() => navigate('/agreements/new')}
              className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] text-xs uppercase tracking-wider font-medium hover:border-[#9E7D3B]"
            >
              Draft First Agreement
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF8F5] border-b border-[#E5E0D8] text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold">
                <tr>
                  <th className="py-3 px-4">Agreement Ref</th>
                  <th className="py-3 px-4">Client Dossier</th>
                  <th className="py-3 px-4">Wedding Details</th>
                  <th className="py-3 px-4">Commercials</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Signing</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E0D8]">
                {agreements.map((a) => (
                  <tr 
                    key={a.id} 
                    onClick={() => navigate(`/agreements/${a.id}`)}
                    className="hover:bg-[#FAF8F5] cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-semibold text-[#1F2421]">
                      {a.agreement_number}
                      <div className="text-[10px] text-[#8C877D] font-sans">v{a.current_version_number}.0</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#1F2421]">
                        {a.client_partner1_name} & {a.client_partner2_name}
                      </div>
                      <div className="text-[11px] text-[#8C877D]">{a.client_email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 text-[#1F2421]">
                        <Calendar size={12} className="text-[#9E7D3B]" />
                        <span>{new Date(a.wedding_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                      </div>
                      <div className="text-[11px] text-[#8C877D]">{a.wedding_location}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#1F2421]">
                        ₹ {Number(a.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[10px] text-[#8C877D]">{a.service_package}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold border ${getStatusBadge(a.status)}`}>
                        {a.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-medium ${a.signing_status === 'COMPLETED' ? 'text-emerald-700' : a.signing_status === 'SENT' ? 'text-purple-700' : 'text-[#8C877D]'}`}>
                        {a.signing_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#9E7D3B] hover:underline">
                        View Dossier <ArrowRight size={12} />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
