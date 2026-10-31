import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Client, RegistrationStatus } from '../../types/client';
import { Calendar, MapPin, Eye, ArrowUpRight } from 'lucide-react';

interface ClientTableProps {
  clients: Client[];
}

export const getStatusBadgeStyle = (status: RegistrationStatus) => {
  switch (status) {
    case 'Confirmed':
      return 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9]';
    case 'Agreement Pending':
      return 'bg-[#F7F2E7] text-[#826127] border-[#DFD0B1]';
    case 'Registered':
      return 'bg-[#EBF2F7] text-[#295570] border-[#BCD4E6]';
    case 'Registration Pending':
      return 'bg-[#FAF0E6] text-[#8F592B] border-[#E8CEB5]';
    case 'Enquiry':
    default:
      return 'bg-[#F2EFE8] text-[#5C5850] border-[#D9D3C7]';
  }
};

export const ClientTable: React.FC<ClientTableProps> = ({ clients }) => {
  const navigate = useNavigate();

  const handleRowClick = (id: string) => {
    navigate(`/clients/${id}`);
  };

  if (clients.length === 0) {
    return (
      <div className="border border-[#E5E0D8] bg-[#FFFFFF] p-12 text-center">
        <p className="font-serif text-lg text-[#1F2421] mb-2">No matching client records found</p>
        <p className="text-xs text-[#736F68]">Adjust your search query or status filter to view clients.</p>
      </div>
    );
  }

  return (
    <div className="border border-[#E5E0D8] bg-[#FFFFFF] overflow-x-auto">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="bg-[#FAF8F5] border-b border-[#E5E0D8] text-[11px] font-semibold tracking-wider text-[#736F68] uppercase">
            <th className="py-3.5 px-4">Client / Couple Name</th>
            <th className="py-3.5 px-4 hidden md:table-cell">Contact Details</th>
            <th className="py-3.5 px-4">Wedding Date</th>
            <th className="py-3.5 px-4 hidden lg:table-cell">Venue & City</th>
            <th className="py-3.5 px-4">Status</th>
            <th className="py-3.5 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#E5E0D8]">
          {clients.map((client) => {
            return (
              <tr
                key={client.id}
                onClick={() => handleRowClick(client.id)}
                className="hover:bg-[#FAF8F5] transition-colors cursor-pointer group"
              >
                {/* Couple Name */}
                <td className="py-4 px-4">
                  <div className="font-serif text-base font-semibold text-[#1F2421] group-hover:text-[#9E7D3B] transition-colors flex items-center gap-1.5">
                    <span>{client.partner1Name} & {client.partner2Name}</span>
                    <ArrowUpRight size={13} className="opacity-0 group-hover:opacity-100 transition-opacity text-[#9E7D3B]" />
                  </div>
                  <div className="text-[11px] text-[#8C877D] tracking-wide mt-0.5">
                    ID: {client.id} · {client.servicePackage}
                  </div>
                </td>

                {/* Contact info */}
                <td className="py-4 px-4 hidden md:table-cell">
                  <div className="text-[#1F2421] font-medium">{client.email}</div>
                  <div className="text-[#736F68] text-[11px] mt-0.5">{client.phone}</div>
                </td>

                {/* Wedding Date */}
                <td className="py-4 px-4 whitespace-nowrap">
                  <div className="flex items-center gap-1.5 text-[#1F2421] font-medium">
                    <Calendar size={13} className="text-[#9E7D3B]" />
                    <span>
                      {new Date(client.weddingDate).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#736F68] mt-0.5">
                    {client.expectedGuestCount} Guests · {client.estimatedBudget}
                  </div>
                </td>

                {/* Location */}
                <td className="py-4 px-4 hidden lg:table-cell">
                  <div className="flex items-center gap-1.5 text-[#1F2421]">
                    <MapPin size={13} className="text-[#9E7D3B] shrink-0" />
                    <span className="truncate max-w-[220px]">{client.weddingLocation}</span>
                  </div>
                  <div className="text-[11px] text-[#8C877D] truncate max-w-[220px] mt-0.5">
                    Theme: {client.weddingTheme}
                  </div>
                </td>

                {/* Status Badge */}
                <td className="py-4 px-4 whitespace-nowrap">
                  <span className={`inline-block px-2.5 py-1 text-[10px] uppercase tracking-wider font-semibold border ${getStatusBadgeStyle(client.status)}`}>
                    {client.status}
                  </span>
                </td>

                {/* Actions */}
                <td className="py-4 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleRowClick(client.id)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-[11px] uppercase tracking-wider text-[#1F2421] bg-[#FAF8F5] hover:bg-[#1F2421] hover:text-[#FAF8F5] border border-[#E5E0D8] transition-colors"
                  >
                    <Eye size={12} />
                    <span>View Dossier</span>
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

