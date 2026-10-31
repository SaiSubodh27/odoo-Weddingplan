import React, { useEffect, useRef, useState } from 'react';
import { Menu, Plus, Bell, Calendar } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useClients } from '../../context/ClientContext';

interface TopbarProps {
  onToggleSidebar: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleSidebar }) => {
  const { currentUser } = useClients();
  const location = useLocation();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const notificationsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setNotificationsOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.startsWith('/inbox')) return 'Gmail Inbox and Review Queue';
    if (path.startsWith('/enquiries/new')) return 'Record Inbound Enquiry';
    if (path.startsWith('/enquiries/') && path !== '/enquiries') return 'Enquiry Dossier and Registration';
    if (path.startsWith('/enquiries')) return 'Enquiries and Lead Management';
    if (path.startsWith('/clients/new')) return 'New Client Registration';
    if (path.startsWith('/clients/') && path !== '/clients') return 'Client Dossier';
    if (path.startsWith('/clients')) return 'Client Directory';
    if (path.startsWith('/vendors')) return 'Vendor Directory';
    if (path.startsWith('/quotations')) return 'Wedding Quotations';
    if (path.startsWith('/weddings')) return 'Wedding Schedule and Venues';
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

        {/* Notifications empty state until a notification feed is connected */}
        <div ref={notificationsRef} className="relative">
          <button
            type="button"
            onClick={() => setNotificationsOpen(open => !open)}
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            aria-controls="rk-notifications-panel"
            className="border border-[#E5E0D8] p-2 text-[#5C5850] bg-[#FAF8F5] hover:bg-[#F2EFE8]"
          >
            <Bell size={16} />
          </button>
          {notificationsOpen && (
            <div id="rk-notifications-panel" role="region" aria-label="Notifications" className="absolute right-0 top-full mt-2 w-72 max-w-[calc(100vw-2rem)] bg-white border border-[#E5E0D8] shadow-lg z-50">
              <div className="px-4 py-3 border-b border-[#E5E0D8] text-sm font-semibold text-[#1F2421]">Notifications</div>
              <div className="px-5 py-8 text-center">
                <Bell size={22} className="mx-auto mb-3 text-[#B6A48C]" />
                <p className="text-sm font-medium text-[#1F2421]">No new notifications</p>
                <p className="mt-1 text-xs text-[#736F68]">You're all caught up.</p>
              </div>
            </div>
          )}
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

