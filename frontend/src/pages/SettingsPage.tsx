import React from 'react';
import { useClients } from '../context/ClientContext';
import { Building, MapPin, Shield, Check } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { currentUser } = useClients();

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-6 border-b border-[#E5E0D8]">
        <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
          Configuration and Preferences
        </div>
        <h1 className="font-serif text-3xl text-[#1F2421]">Agency System Settings</h1>
        <p className="text-xs text-[#736F68] mt-1">
          Operating parameters for The Royal Knot luxury wedding planning operations.
        </p>
      </div>

      {/* Agency Identity */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
          <Building size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">Agency Profile</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Agency Name
            </label>
            <input
              type="text"
              readOnly
              value="The Royal Knot — Luxury Wedding Planners"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Operating Headquarters
            </label>
            <input
              type="text"
              readOnly
              value="Jaipur and Udaipur, Rajasthan, India"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Current Logged-in Staff
            </label>
            <input
              type="text"
              readOnly
              value={`${currentUser.name} (${currentUser.role})`}
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Official Contact Email
            </label>
            <input
              type="text"
              readOnly
              value="concierge@theroyalknot.in"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>
        </div>
      </div>

      {/* Flagship Hubs */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
          <MapPin size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">Regional Operations Hubs</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5]">
            <div className="flex items-center justify-between mb-2">
              <span className="font-serif text-base font-semibold text-[#1F2421]">Jaipur Flagship Hub</span>
              <span className="text-[10px] text-[#2D5A3C] bg-[#EBF3ED] px-2 py-0.5 border border-[#C3D9C9] font-medium">Active</span>
            </div>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Rambagh Palace Circle, C-Scheme, Jaipur, Rajasthan 302001
            </p>
          </div>

          <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5]">
            <div className="flex items-center justify-between mb-2">
              <span className="font-serif text-base font-semibold text-[#1F2421]">Udaipur Lake Hub</span>
              <span className="text-[10px] text-[#2D5A3C] bg-[#EBF3ED] px-2 py-0.5 border border-[#C3D9C9] font-medium">Active</span>
            </div>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Pichola Promenade, Haridas Ji Ki Magri, Udaipur, Rajasthan 313001
            </p>
          </div>
        </div>
      </div>

      {/* System Status info */}
      <div className="p-4 bg-[#FFFFFF] border border-[#E5E0D8] flex items-center justify-between text-xs text-[#736F68]">
        <div className="flex items-center gap-2">
          <Shield size={14} className="text-[#9E7D3B]" />
          <span>System Environment: Frontend Standalone Preview (Mock Mode)</span>
        </div>
        <div className="flex items-center gap-1 text-[#2D5A3C]">
          <Check size={14} />
          <span className="font-medium">Data Storage Synchronized</span>
        </div>
      </div>
    </div>
  );
};
