import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { ClientTable } from '../components/clients/ClientTable';
import { RegistrationStatus } from '../types/client';
import { Search, Plus, Filter, RotateCcw } from 'lucide-react';

export const ClientsPage: React.FC = () => {
  const { clients } = useClients();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const statusOptions: ('All' | RegistrationStatus)[] = [
    'All',
    'Enquiry',
    'Registration Pending',
    'Registered',
    'Agreement Pending',
    'Confirmed'
  ];

  const filteredClients = useMemo(() => {
    return clients.filter((client) => {
      const matchesSearch =
        client.partner1Name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.partner2Name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.phone.includes(searchTerm) ||
        client.weddingLocation.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.id.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === 'All' || client.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [clients, searchTerm, statusFilter]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setStatusFilter('All');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div>
          <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
            Registry & Portfolios
          </div>
          <h1 className="font-serif text-3xl text-[#1F2421]">Clients Directory</h1>
          <p className="text-xs text-[#736F68] mt-1">
            Managing {clients.length} destination wedding dossiers across Jaipur and Udaipur.
          </p>
        </div>

        <Link
          to="/clients/new"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors"
        >
          <Plus size={14} className="text-[#D9C496]" />
          <span>Add New Client</span>
        </Link>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by couple name, reference ID, phone, email, or palace..."
            className="w-full pl-9 pr-3.5 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-[#736F68] px-2">
            <Filter size={13} className="text-[#9E7D3B]" />
            <span className="uppercase tracking-wider text-[11px] font-medium hidden sm:inline">Status:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          >
            {statusOptions.map((st) => (
              <option key={st} value={st}>
                {st === 'All' ? 'All Statuses' : st}
              </option>
            ))}
          </select>

          {(searchTerm || statusFilter !== 'All') && (
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

      {/* Result stats summary */}
      <div className="flex items-center justify-between text-xs text-[#736F68] px-1">
        <span>
          Showing <strong className="text-[#1F2421]">{filteredClients.length}</strong> of{' '}
          <strong className="text-[#1F2421]">{clients.length}</strong> clients
        </span>
        {statusFilter !== 'All' && (
          <span className="text-[11px] text-[#9E7D3B]">
            Filtered by: <strong>{statusFilter}</strong>
          </span>
        )}
      </div>

      {/* Table */}
      <ClientTable clients={filteredClients} />
    </div>
  );
};

