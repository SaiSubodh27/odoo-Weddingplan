import React, { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Inbox, Clock3, Users, ClipboardCheck, CalendarDays, ArrowRight, MapPin } from 'lucide-react';
import { enquiryApi } from '../services/api';
import { useClients } from '../context/ClientContext';

type NewEnquiry = { id: string; clientName: string; status: string };
export const DashboardPage: React.FC = () => {
  const { clients, currentUser } = useClients();
  const isClient = currentUser?.role?.toLowerCase().includes('client');
  if (isClient) {
    return <Navigate to="/client-portal" replace />;
  }

  const [enquiries, setEnquiries] = useState<NewEnquiry[]>([]);
  useEffect(() => {
    let mounted = true;
    enquiryApi.list({ pageSize: 100 }).then(result => {
      if (mounted) setEnquiries((result.items || []).filter((e: NewEnquiry) => e.status === 'New'));
    }).catch(() => { if (mounted) setEnquiries([]); });
    return () => { mounted = false; };
  }, []);
  const pending = clients.filter(c => c.status === 'Registration Pending' || c.status === 'Agreement Pending');
  const active = clients.filter(c => c.status === 'Confirmed');
  const weddings = [...active].filter(c => !Number.isNaN(new Date(c.weddingDate).getTime())).sort((a,b) => new Date(a.weddingDate).getTime() - new Date(b.weddingDate).getTime()).slice(0,3);
  const stats = [
    { title: 'New Enquiries', value: enquiries.length, detail: 'Prospective couples awaiting first contact', icon: Inbox, to: '/enquiries' },
    { title: 'Pending Requests', value: pending.length, detail: 'Registrations and agreements requiring action', icon: Clock3, to: '/enquiries' },
    { title: 'Active Clients', value: active.length, detail: 'Confirmed clients in the planning pipeline', icon: Users, to: '/clients?status=Confirmed' },
  ];
  return <div className="rk-overview">
    <div className="rk-overview-intro"><MapPin size={19}/><span>Luxury Destination Concierge</span></div>
    <div className="rk-overview-stats">
      {stats.map(s => <Link key={s.title} to={s.to} className="rk-overview-stat">
        <div className="rk-overview-stat-head"><span className="rk-stat-icon"><s.icon size={25}/></span><h2>{s.title}</h2></div>
        <strong>{s.value}</strong><p>{s.detail}</p>
      </Link>)}
    </div>
    <div className="rk-overview-panels">
      <section className="rk-overview-panel">
        <h2><ClipboardCheck size={27}/> Action Required</h2>
        <div className="rk-overview-action-list">
          {pending.slice(0,4).map(c => <Link key={c.id} to={'/clients/'+c.id} className="rk-overview-action">
            <span><b>{c.partner1Name} and {c.partner2Name}</b><small>{c.status}</small></span><ArrowRight size={20}/>
          </Link>)}
          {enquiries.slice(0,3).map(e => <Link key={e.id} to={'/enquiries/'+e.id} className="rk-overview-action">
            <span><b>{e.clientName}</b><small>New enquiry to review</small></span><ArrowRight size={20}/>
          </Link>)}
          {pending.length===0 && enquiries.length===0 && <p className="rk-overview-empty">No outstanding enquiries or registration requests.</p>}
        </div>
      </section>
      <section className="rk-overview-panel">
        <h2><CalendarDays size={27}/> Upcoming Weddings</h2>
        <div className="rk-overview-wedding-list">
          {weddings.map(w => <Link key={w.id} to={'/weddings/'+w.id} className="rk-overview-wedding">
            <b>{w.partner1Name} and {w.partner2Name}</b>
            <small><CalendarDays size={14}/>{new Date(w.weddingDate).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})} · {w.weddingLocation}</small>
          </Link>)}
          {weddings.length===0 && <p className="rk-overview-empty">No confirmed weddings scheduled yet.</p>}
        </div>
      </section>
    </div>
  </div>;
};
