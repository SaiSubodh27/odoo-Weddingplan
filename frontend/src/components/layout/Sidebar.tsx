import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Inbox,
  Users, 
  HeartHandshake, 
  Settings, 
  LogOut,
  Sparkles,
  MapPin
} from 'lucide-react';
import { useClients } from '../../context/ClientContext';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { logout } = useClients();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Enquiries', path: '/enquiries', icon: Inbox },
    { name: 'Clients', path: '/clients', icon: Users },
    { name: 'Weddings', path: '/weddings', icon: HeartHandshake },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#FAF8F5] border-r border-[#E5E0D8]
        flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Brand Header */}
        <div className="h-20 px-6 border-b border-[#E5E0D8] flex items-center justify-between bg-[#FFFFFF]">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-[#9E7D3B] text-lg font-serif">✦</span>
              <span className="font-serif text-xl tracking-wider font-semibold text-[#1F2421] uppercase">
                The Royal Knot
              </span>
            </div>
            <span className="text-[10px] tracking-[0.2em] uppercase text-[#736F68] font-medium pl-5">
              Jaipur · Udaipur
            </span>
          </div>
        </div>

        {/* Agency Tagline */}
        <div className="px-6 py-4 bg-[#F5F2EB] border-b border-[#E5E0D8] flex items-center gap-2 text-[#736F68] text-xs">
          <MapPin size={13} className="text-[#9E7D3B] shrink-0" />
          <span className="tracking-wide text-[11px]">Luxury Destination Concierge</span>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          <div className="text-[10px] font-semibold text-[#8C877D] uppercase tracking-[0.15em] px-3 mb-2">
            Agency Management
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) => `
                  flex items-center gap-3 px-3 py-3 text-xs tracking-wider uppercase font-medium
                  border border-transparent transition-colors
                  ${isActive 
                    ? 'bg-[#FFFFFF] text-[#1F2421] border-[#E5E0D8] font-semibold shadow-none' 
                    : 'text-[#5C5850] hover:bg-[#F2EFE8] hover:text-[#1F2421]'
                  }
                `}
              >
                <Icon size={16} className="text-[#9E7D3B]" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Agency System Info card */}
        <div className="p-4 mx-4 mb-4 border border-[#E5E0D8] bg-[#FFFFFF]">
          <div className="flex items-center gap-2 text-[#9E7D3B] text-xs font-serif font-semibold mb-1">
            <Sparkles size={13} />
            <span>Winter Season '26</span>
          </div>
          <p className="text-[11px] text-[#736F68] leading-relaxed">
            High destination wedding intake active across Rajasthan heritage properties.
          </p>
        </div>

        {/* User Session & Logout */}
        <div className="p-4 border-t border-[#E5E0D8] bg-[#FFFFFF]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 text-xs uppercase tracking-wider text-[#736F68] hover:text-[#1F2421] hover:bg-[#F5F2EB] border border-[#E5E0D8] transition-colors"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};

