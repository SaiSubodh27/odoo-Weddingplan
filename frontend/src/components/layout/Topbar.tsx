import React from 'react';
import { Menu, Plus, Bell, Calendar } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useClients } from '../../context/ClientContext';

interface TopbarProps {
  onToggleSidebar: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleSidebar }) => {
  const { currentUser } = useClients();
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.startsWith('/inbox')) return 'Gmail Inbox & Review Queue';
    if (path.startsWith('/enquiries/new')) return 'Record Inbound Enquiry';
    if (path.startsWith('/enquiries/') && path !== '/enquiries') return 'Enquiry Dossier & Registration';
    if (path.startsWith('/enquiries')) return 'Enquiries & Lead Management';
    if (path.startsWith('/clients/new')) return 'New Client Registration';
    if (path.startsWith('/clients/') && path !== '/clients') return 'Client Dossier';
    if (path.startsWith('/clients')) return 'Client Directory';
    if (path.startsWith('/weddings')) return 'Wedding Schedule & Venues';
    if (path.startsWith('/settings')) return 'Agency Settings';
    return 'Executive Overview';
  };

  const currentDate = new Intl.DateTimeFormat('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }).format(new Date());

  return (
    <header className="h-20 bg-[#FFFFFF] border-b border-[#E5E0D8] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-4">
        {/* Mobile menu trigger */}
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-[#1F2421] border border-[#E5E0D8] hover:bg-[#FAF8F5]"
          aria-label="Toggle menu"
        >
          <Menu size={18} />
        </button>

        <div>
          <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
            The Royal Knot System
          </div>
          <h1 className="text-xl sm:text-2xl font-serif text-[#1F2421] tracking-tight">
            {getPageTitle()}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-6">
        {/* Date display */}
        <div className="hidden md:flex items-center gap-2 text-xs text-[#736F68] border border-[#E5E0D8] px-3 py-1.5 bg-[#FAF8F5]">
          <Calendar size={13} className="text-[#9E7D3B]" />
          <span>{currentDate}</span>
        </div>

        {/* Quick action button */}
        <Link
          to="/clients/new"
          className="flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-medium hover:bg-[#343733] border border-[#1F2421] transition-colors"
        >
          <Plus size={14} className="text-[#D9C496]" />
          <span className="hidden sm:inline">Add Client</span>
          <span className="sm:hidden">Add</span>
        </Link>

        {/* Notifications mock icon */}
        <div className="relative border border-[#E5E0D8] p-2 text-[#5C5850] bg-[#FAF8F5] cursor-pointer hover:bg-[#F2EFE8]">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-[#9E7D3B]" />
        </div>

        {/* User profile */}
        <div className="flex items-center gap-3 pl-3 sm:pl-4 border-l border-[#E5E0D8]">
          <div className="w-8 h-8 bg-[#F2EFE8] border border-[#E5E0D8] flex items-center justify-center font-serif text-sm font-semibold text-[#9E7D3B]">
            {currentUser.name.charAt(0)}
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-medium text-[#1F2421]">{currentUser.name}</div>
            <div className="text-[10px] uppercase tracking-wider text-[#8C877D]">{currentUser.role}</div>
          </div>
        </div>
      </div>
    </header>
  );
};

