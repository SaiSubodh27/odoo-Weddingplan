import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { 
  Users, 
  HeartHandshake, 
  Clock, 
  ArrowRight, 
  Calendar, 
  MapPin, 
  Sparkles,
  Mail,
  Plus
} from 'lucide-react';
import { getStatusBadgeStyle } from '../components/clients/ClientTable';

export const DashboardPage: React.FC = () => {
  const { clients, currentUser } = useClients();
  const navigate = useNavigate();

  // Metrics calculation
  const totalClients = clients.length;
  const confirmedWeddings = clients.filter(c => c.status === 'Confirmed' || c.status === 'Agreement Pending').length;
  const pendingRegistrations = clients.filter(c => c.status === 'Registration Pending' || c.status === 'Enquiry').length;

  // Recent enquiries (latest 4)
  const recentEnquiries = clients.slice(0, 4);

  // Upcoming weddings sorted by date
  const upcomingWeddings = [...clients]
    .sort((a, b) => new Date(a.weddingDate).getTime() - new Date(b.weddingDate).getTime())
    .slice(0, 3);

  const getDaysUntil = (dateStr: string) => {
    const today = new Date();
    const target = new Date(dateStr);
    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#9E7D3B] font-medium mb-1">
            <Sparkles size={13} />
            <span>Winter Royal Wedding Season</span>
          </div>
          <h1 className="font-serif text-2xl sm:text-3xl text-[#1F2421]">
            Welcome, {currentUser.name}
          </h1>
          <p className="text-xs text-[#736F68] mt-1 max-w-2xl leading-relaxed">
            Agency overview for high-heritage destination weddings across Jaipur & Udaipur. All systems operational.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/enquiries/new"
            className="flex items-center gap-2 px-4 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors"
          >
            <Plus size={14} className="text-[#D9C496]" />
            <span>Record Enquiry</span>
          </Link>
          <Link
            to="/enquiries"
            className="flex items-center gap-2 px-4 py-2.5 bg-[#FAF8F5] text-[#1F2421] text-xs uppercase tracking-wider font-medium hover:bg-[#F2EFE8] border border-[#E5E0D8] transition-colors"
          >
            <span>Enquiry Intake</span>
          </Link>
          <Link
            to="/clients"
            className="flex items-center gap-2 px-4 py-2.5 bg-[#FAF8F5] text-[#1F2421] text-xs uppercase tracking-wider font-medium hover:bg-[#F2EFE8] border border-[#E5E0D8] transition-colors"
          >
            <span>Client Directory</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Clients */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs uppercase tracking-wider text-[#736F68] font-medium">
              Total Client Dossiers
            </span>
            <div className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B]">
              <Users size={16} />
            </div>
          </div>
          <div className="font-serif text-3xl sm:text-4xl text-[#1F2421] font-semibold mb-1">
            {totalClients}
          </div>
          <div className="flex items-center justify-between text-[11px] text-[#736F68] pt-2 border-t border-[#E5E0D8] mt-3">
            <span>Active agency pipeline</span>
            <span className="text-[#2D5A3C] font-medium">100% On Schedule</span>
          </div>
        </div>

        {/* Upcoming Weddings */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs uppercase tracking-wider text-[#736F68] font-medium">
              Upcoming Palace Weddings
            </span>
            <div className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B]">
              <HeartHandshake size={16} />
            </div>
          </div>
          <div className="font-serif text-3xl sm:text-4xl text-[#1F2421] font-semibold mb-1">
            {confirmedWeddings}
          </div>
          <div className="flex items-center justify-between text-[11px] text-[#736F68] pt-2 border-t border-[#E5E0D8] mt-3">
            <span>Confirmed or pending contract</span>
            <span className="text-[#9E7D3B] font-medium">Jaipur & Udaipur</span>
          </div>
        </div>

        {/* Pending Registrations */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs uppercase tracking-wider text-[#736F68] font-medium">
              Pending Registrations
            </span>
            <div className="p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B]">
              <Clock size={16} />
            </div>
          </div>
          <div className="font-serif text-3xl sm:text-4xl text-[#1F2421] font-semibold mb-1">
            {pendingRegistrations}
          </div>
          <div className="flex items-center justify-between text-[11px] text-[#736F68] pt-2 border-t border-[#E5E0D8] mt-3">
            <span>Enquiries awaiting review</span>
            <span className="text-[#8F592B] font-medium">Action Required</span>
          </div>
        </div>
      </div>

      {/* Grid of Sections: Upcoming Wedding Schedule & Recent Enquiries */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Upcoming Wedding Schedule (Left 7 Cols) */}
        <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#E5E0D8] p-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8] mb-6">
            <div>
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
                Production Timeline
              </div>
              <h2 className="font-serif text-xl text-[#1F2421]">Upcoming Wedding Schedule</h2>
            </div>
            <Link
              to="/weddings"
              className="text-xs uppercase tracking-wider text-[#1F2421] hover:text-[#9E7D3B] flex items-center gap-1 font-medium"
            >
              <span>View Full Calendar</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          <div className="space-y-4">
            {upcomingWeddings.map((wedding) => {
              const daysLeft = getDaysUntil(wedding.weddingDate);
              return (
                <div
                  key={wedding.id}
                  onClick={() => navigate(`/clients/${wedding.id}`)}
                  className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] hover:border-[#1F2421] cursor-pointer transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div>
                      <div className="font-serif text-base font-semibold text-[#1F2421]">
                        {wedding.partner1Name} & {wedding.partner2Name}
                      </div>
                      <div className="text-[11px] text-[#8C877D] tracking-wide">
                        Ref: {wedding.id} · {wedding.servicePackage}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold border ${getStatusBadgeStyle(wedding.status)}`}>
                        {wedding.status}
                      </span>
                      <div className="px-2 py-0.5 bg-[#FFFFFF] border border-[#E5E0D8] text-[10px] text-[#736F68] font-medium">
                        {daysLeft} Days to go
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#5C5850] pt-2 border-t border-[#E5E0D8]/60">
                    <div className="flex items-center gap-1.5 truncate">
                      <MapPin size={12} className="text-[#9E7D3B] shrink-0" />
                      <span className="truncate">{wedding.weddingLocation}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar size={12} className="text-[#9E7D3B] shrink-0" />
                      <span>
                        {new Date(wedding.weddingDate).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })}
                      </span>
                    </div>
                  </div>

                  <div className="mt-2 text-[11px] text-[#736F68] italic truncate">
                    Aesthetic: "{wedding.weddingTheme}"
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Client Enquiries (Right 5 Cols) */}
        <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#E5E0D8] p-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8] mb-6">
            <div>
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
                Inbound Desk
              </div>
              <h2 className="font-serif text-xl text-[#1F2421]">Recent Client Enquiries</h2>
            </div>
            <Link
              to="/clients"
              className="text-xs uppercase tracking-wider text-[#1F2421] hover:text-[#9E7D3B] flex items-center gap-1 font-medium"
            >
              <span>All Clients</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          <div className="space-y-3.5">
            {recentEnquiries.map((enquiry) => (
              <div
                key={enquiry.id}
                onClick={() => navigate(`/clients/${enquiry.id}`)}
                className="p-3.5 border border-[#E5E0D8] hover:bg-[#FAF8F5] cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-serif text-sm font-semibold text-[#1F2421]">
                    {enquiry.partner1Name} & {enquiry.partner2Name}
                  </span>
                  <span className={`text-[9px] uppercase px-1.5 py-0.5 border ${getStatusBadgeStyle(enquiry.status)}`}>
                    {enquiry.status}
                  </span>
                </div>

                <div className="text-[11px] text-[#736F68] space-y-1 mt-1.5">
                  <div className="flex items-center gap-1.5">
                    <Mail size={11} className="text-[#9E7D3B]" />
                    <span className="truncate">{enquiry.email}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-[#8C877D] pt-1 border-t border-[#E5E0D8]/40">
                    <span>Source: {enquiry.enquirySource}</span>
                    <span>Budget: {enquiry.estimatedBudget}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-[#E5E0D8]">
            <Link
              to="/clients/new"
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#FAF8F5] hover:bg-[#F2EFE8] text-[#1F2421] border border-[#E5E0D8] text-xs uppercase tracking-wider font-medium transition-colors"
            >
              <Plus size={13} />
              <span>Register Inbound Enquiry</span>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
};
