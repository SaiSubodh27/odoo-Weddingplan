import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Enquiry, EnquiryStatus, EnquirySource } from '../types/enquiry';
import { enquiryApi } from '../services/api';
import { 
  Search, 
  Plus, 
  Filter, 
  Mail, 
  Phone, 
  Calendar, 
  MapPin, 
  Eye, 
  RotateCcw,
  Globe
} from 'lucide-react';

export const getEnquiryStatusBadge = (status: EnquiryStatus) => {
  switch (status) {
    case 'Registered':
    case 'Approved':
      return 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9] font-semibold';
    case 'Under Review':
      return 'bg-[#FDF6E2] text-[#8C6D1F] border-[#E8D49E] font-semibold';
    case 'Registration Submitted':
      return 'bg-[#F0F4FA] text-[#1D4E89] border-[#B5CEEB] font-semibold';
    case 'Corrections Requested':
      return 'bg-[#FFF3E8] text-[#B85D1B] border-[#FAD3B4] font-semibold';
    case 'Registration Link Sent':
    case 'Registration Document Sent':
      return 'bg-[#F7F2E7] text-[#826127] border-[#DFD0B1]';
    case 'Registration Received':
      return 'bg-[#EBF2F7] text-[#295570] border-[#BCD4E6]';
    case 'Contacted':
      return 'bg-[#FAF0E6] text-[#8F592B] border-[#E8CEB5]';
    case 'Closed':
      return 'bg-[#F2EFE8] text-[#8C877D] border-[#D9D3C7]';
    case 'New':
    default:
      return 'bg-[#FAF8F5] text-[#1F2421] border-[#9E7D3B] font-bold';
  }
};

export const getSourceIcon = (source: EnquirySource) => {
  switch (source) {
    case 'Phone':
      return <Phone size={12} className="text-[#9E7D3B]" />;
    case 'Website':
      return <Globe size={12} className="text-[#9E7D3B]" />;
    case 'Email':
    default:
      return <Mail size={12} className="text-[#9E7D3B]" />;
  }
};

export const EnquiriesPage: React.FC = () => {
  const navigate = useNavigate();
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [sourceFilter, setSourceFilter] = useState<string>('All');

  const fetchEnquiries = async () => {
    setIsLoading(true);
    try {
      const data = await enquiryApi.list({
        search: searchTerm || undefined,
        status: statusFilter,
        source: sourceFilter,
        pageSize: 100
      });
      setEnquiries(data.items || []);
    } catch {
      // Fallback empty if backend offline
      setEnquiries([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEnquiries();
  }, [statusFilter, sourceFilter]);

  // Client-side quick filter on search query
  const filteredEnquiries = useMemo(() => {
    if (!searchTerm.trim()) return enquiries;
    const term = searchTerm.toLowerCase();
    return enquiries.filter(e =>
      e.clientName.toLowerCase().includes(term) ||
      e.email.toLowerCase().includes(term) ||
      e.phone.includes(term) ||
      (e.weddingLocation && e.weddingLocation.toLowerCase().includes(term)) ||
      e.id.toLowerCase().includes(term)
    );
  }, [enquiries, searchTerm]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setStatusFilter('All');
    setSourceFilter('All');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div>
          <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
            Inbound Inquiries & Lead Management
          </div>
          <h1 className="font-serif text-3xl text-[#1F2421]">Wedding Enquiries</h1>
          <p className="text-xs text-[#736F68] mt-1">
            Tracking luxury email and phone enquiries before client dossier registration.
          </p>
        </div>

        <Link
          to="/enquiries/new"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors"
        >
          <Plus size={14} className="text-[#D9C496]" />
          <span>Record New Enquiry</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search enquiries by client name, email, phone, venue, or ref..."
            className="w-full pl-9 pr-3.5 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-[#736F68]">
            <Filter size={13} className="text-[#9E7D3B]" />
            <span className="uppercase tracking-wider text-[10px] font-medium">Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          >
            <option value="All">All Statuses</option>
            <option value="New">New</option>
            <option value="Contacted">Contacted</option>
            <option value="Registration Document Sent">Registration Document Sent</option>
            <option value="Registration Received">Registration Received</option>
            <option value="Under Review">Under Review</option>
            <option value="Registered">Registered</option>
            <option value="Closed">Closed</option>
          </select>

          {/* Source Filter */}
          <div className="flex items-center gap-1.5 text-xs text-[#736F68] pl-2 border-l border-[#E5E0D8]">
            <span className="uppercase tracking-wider text-[10px] font-medium">Source:</span>
          </div>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-2.5 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          >
            <option value="All">All Sources</option>
            <option value="Email">Email</option>
            <option value="Phone">Phone</option>
            <option value="Website">Website</option>
          </select>

          {(searchTerm || statusFilter !== 'All' || sourceFilter !== 'All') && (
            <button
              onClick={handleResetFilters}
              title="Reset Filters"
              className="p-2 border border-[#E5E0D8] text-[#736F68] hover:text-[#1F2421] hover:bg-[#FAF8F5]"
            >
              <RotateCcw size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-[#736F68] px-1">
        <span>
          Showing <strong className="text-[#1F2421]">{filteredEnquiries.length}</strong> enquiries
        </span>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 bg-[#9E7D3B]" /> Manual Staff Intake Active</span>
        </div>
      </div>

      {/* Enquiries Table */}
      {isLoading ? (
        <div className="p-12 text-center bg-[#FFFFFF] border border-[#E5E0D8] text-xs text-[#736F68]">
          Loading palace enquiries...
        </div>
      ) : filteredEnquiries.length === 0 ? (
        <div className="border border-[#E5E0D8] bg-[#FFFFFF] p-12 text-center">
          <p className="font-serif text-lg text-[#1F2421] mb-2">No enquiries found</p>
          <p className="text-xs text-[#736F68] mb-4">No matching records found for the selected criteria.</p>
          <Link
            to="/enquiries/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold"
          >
            <Plus size={13} />
            <span>Record First Enquiry</span>
          </Link>
        </div>
      ) : (
        <div className="border border-[#E5E0D8] bg-[#FFFFFF] overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#FAF8F5] border-b border-[#E5E0D8] text-[11px] font-semibold tracking-wider text-[#736F68] uppercase">
                <th className="py-3.5 px-4">Ref ID & Client Name</th>
                <th className="py-3.5 px-4">Source</th>
                <th className="py-3.5 px-4 hidden md:table-cell">Contact</th>
                <th className="py-3.5 px-4">Target Date & Location</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D8]">
              {filteredEnquiries.map((enq) => (
                <tr
                  key={enq.id}
                  onClick={() => navigate(`/enquiries/${enq.id}`)}
                  className="hover:bg-[#FAF8F5] transition-colors cursor-pointer group"
                >
                  <td className="py-4 px-4">
                    <div className="font-serif text-base font-semibold text-[#1F2421] group-hover:text-[#9E7D3B] transition-colors">
                      {enq.clientName}
                    </div>
                    <div className="text-[11px] text-[#8C877D] tracking-wide mt-0.5 font-mono">
                      {enq.id} {enq.clientId ? `· Linked Client: ${enq.clientId}` : ''}
                    </div>
                  </td>

                  <td className="py-4 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-xs text-[#1F2421]">
                      {getSourceIcon(enq.enquirySource)}
                      <span className="font-medium">{enq.enquirySource}</span>
                    </div>
                  </td>

                  <td className="py-4 px-4 hidden md:table-cell">
                    <div className="text-[#1F2421] font-medium">{enq.email}</div>
                    <div className="text-[#736F68] text-[11px] mt-0.5">{enq.phone}</div>
                  </td>

                  <td className="py-4 px-4">
                    <div className="flex items-center gap-1.5 text-[#1F2421] font-medium">
                      <Calendar size={12} className="text-[#9E7D3B]" />
                      <span>{enq.weddingDate || 'Date TBD'}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[#736F68] text-[11px] mt-0.5 truncate max-w-[200px]">
                      <MapPin size={11} className="text-[#9E7D3B] shrink-0" />
                      <span className="truncate">{enq.weddingLocation || 'Rajasthan Heritage'}</span>
                    </div>
                  </td>

                  <td className="py-4 px-4 whitespace-nowrap">
                    <span className={`inline-block px-2.5 py-1 text-[10px] uppercase tracking-wider font-semibold border ${getEnquiryStatusBadge(enq.status)}`}>
                      {enq.status}
                    </span>
                  </td>

                  <td className="py-4 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => navigate(`/enquiries/${enq.id}`)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-[11px] uppercase tracking-wider text-[#1F2421] bg-[#FAF8F5] hover:bg-[#1F2421] hover:text-[#FAF8F5] border border-[#E5E0D8] transition-colors"
                    >
                      <Eye size={12} />
                      <span>Manage</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
