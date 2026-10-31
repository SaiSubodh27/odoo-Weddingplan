import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { VendorDirectoryPage } from './VendorDirectoryPage';
import { Calendar, MapPin, Users, Eye } from 'lucide-react';
import { getStatusBadgeStyle } from '../components/clients/ClientTable';

export const WeddingsPage: React.FC = () => {
  const { clients } = useClients();
  const navigate = useNavigate();
  const [cityFilter, setCityFilter] = useState<'All' | 'Jaipur' | 'Udaipur'>('All');
  const [view,setView]=useState<'projects'|'vendors'>('projects');

  const weddings = clients
    .filter(c => {
      if (cityFilter === 'Jaipur') return c.weddingLocation.toLowerCase().includes('jaipur');
      if (cityFilter === 'Udaipur') return c.weddingLocation.toLowerCase().includes('udaipur');
      return true;
    })
    .sort((a, b) => new Date(a.weddingDate).getTime() - new Date(b.weddingDate).getTime());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div>
          <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
            Production and Venue Calendars
          </div>
          <h1 className="font-serif text-3xl text-[#1F2421]">Palace Weddings Schedule</h1>
          <p className="text-xs text-[#736F68] mt-1">
            Execution dates, heritage venues, and logistics run-sheets for active destination weddings.
          </p>
        </div>

        {/* City Filter */}
        <div className="flex items-center gap-1 bg-[#FFFFFF] border border-[#E5E0D8] p-1">
          {(['All', 'Jaipur', 'Udaipur'] as const).map((city) => (
            <button
              key={city}
              onClick={() => setCityFilter(city)}
              className={`px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                cityFilter === city
                  ? 'bg-[#1F2421] text-[#FAF8F5]'
                  : 'text-[#736F68] hover:text-[#1F2421] hover:bg-[#FAF8F5]'
              }`}
            >
              {city}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2 border-b border-[#E5E0D8] pb-2"><button onClick={()=>setView('projects')} className={'px-4 py-2 text-sm font-semibold '+(view==='projects'?'bg-[#3A312C] text-white':'text-[#6D6257]')}>Wedding Projects</button><button onClick={()=>setView('vendors')} className={'px-4 py-2 text-sm font-semibold '+(view==='vendors'?'bg-[#3A312C] text-white':'text-[#6D6257]')}>Vendor Directory</button></div>
      {view==='vendors'&&<VendorDirectoryPage mode="directory"/>}
      {view==='projects'&&<>
      {/* Grid of Weddings */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {weddings.map((w) => (
          <div
            key={w.id}
            onClick={() => navigate(`/weddings/${w.id}`)}
            className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 hover:border-[#1F2421] cursor-pointer transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className={`px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold border ${getStatusBadgeStyle(w.status)}`}>
                  {w.status}
                </span>
                <span className="text-[11px] font-mono text-[#8C877D]">{w.id}</span>
              </div>

              <h2 className="font-serif text-xl font-semibold text-[#1F2421] mb-1">
                {w.partner1Name} and {w.partner2Name}
              </h2>

              <p className="text-[11px] text-[#9E7D3B] font-medium mb-4">
                {w.servicePackage}
              </p>

              <div className="space-y-2.5 text-xs text-[#5C5850] py-3 border-y border-[#E5E0D8]">
                <div className="flex items-center gap-2">
                  <Calendar size={13} className="text-[#9E7D3B] shrink-0" />
                  <span className="font-medium text-[#1F2421]">
                    {new Date(w.weddingDate).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <MapPin size={13} className="text-[#9E7D3B] shrink-0" />
                  <span className="truncate">{w.weddingLocation}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Users size={13} className="text-[#9E7D3B] shrink-0" />
                  <span>{w.expectedGuestCount} Expected Guests</span>
                </div>
              </div>

              <div className="mt-3">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">
                  Decor Aesthetic
                </span>
                <p className="text-[11px] text-[#1F2421] bg-[#FAF8F5] p-2 border border-[#E5E0D8] line-clamp-2">
                  "{w.weddingTheme}"
                </p>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-[#E5E0D8] flex items-center justify-between text-xs">
              <span className="text-[#736F68]">Budget: <strong className="text-[#1F2421]">{w.estimatedBudget}</strong></span>
              <span className="flex items-center gap-1 text-[#9E7D3B] font-medium hover:underline">
                <span>Open Dossier</span>
                <Eye size={12} />
              </span>
            </div>
          </div>
        ))}
      </div>
      </>}
    </div>
  );
};

