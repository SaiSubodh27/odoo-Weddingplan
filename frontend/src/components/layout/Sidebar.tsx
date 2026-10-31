import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Mail, Inbox, Users, HeartHandshake, Settings, LogOut, Sparkles, MapPin, ChevronDown, BriefcaseBusiness } from 'lucide-react';
import { useClients } from '../../context/ClientContext';

interface SidebarProps { isOpen: boolean; onClose?: () => void; }
export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { logout } = useClients();
  const navigate = useNavigate();
  const location = useLocation();
  const inWorkspace = ['/inbox','/enquiries','/clients'].some(path => location.pathname.startsWith(path));
  const [expanded, setExpanded] = useState(true);
  const handleLogout = () => { logout(); navigate('/login'); };
  const main = [
    {name:'Dashboard',path:'/dashboard',icon:LayoutDashboard},
    {name:'Weddings',path:'/weddings',icon:HeartHandshake},
    {name:'Settings',path:'/settings',icon:Settings},
  ];
  const workspace = [
    {name:'Email Inbox',path:'/inbox',icon:Mail},
    {name:'Enquiries',path:'/enquiries',icon:Inbox},
    {name:'Clients',path:'/clients',icon:Users},
  ];
  const navClass = (active:boolean) => 'rk-side-link flex items-center gap-3 px-3 py-3 text-xs tracking-wider uppercase font-medium border border-transparent transition-colors ' +
    (active?'bg-[#FFFFFF] text-[#1F2421] border-[#E5E0D8] font-semibold shadow-none':'text-[#5C5850] hover:bg-[#F2EFE8] hover:text-[#1F2421]');
  return <>
    {isOpen && <div className="fixed inset-0 bg-black/20 z-40 lg:hidden" onClick={onClose}/>}
    <aside className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#FAF8F5] border-r border-[#E5E0D8] flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${isOpen?'translate-x-0':'-translate-x-full lg:translate-x-0'}`}>
      <div className="h-20 px-6 border-b border-[#E5E0D8] flex items-center justify-between bg-[#FFFFFF]">
        <div className="flex flex-col"><div className="flex items-center gap-2"><span className="text-[#9E7D3B] text-lg font-serif">✦</span><span className="font-serif text-xl tracking-wider font-semibold text-[#1F2421] uppercase">The Royal Knot</span></div><span className="text-[10px] tracking-[0.2em] uppercase text-[#736F68] font-medium pl-5">Jaipur · Udaipur</span></div>
      </div>
      <div className="px-6 py-4 bg-[#F5F2EB] border-b border-[#E5E0D8] flex items-center gap-2 text-[#736F68] text-xs"><MapPin size={13} className="text-[#9E7D3B] shrink-0"/><span className="tracking-wide text-[11px]">Luxury Destination Concierge</span></div>
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        <div className="text-[10px] font-semibold text-[#8C877D] uppercase tracking-[0.15em] px-3 mb-2">Agency Management</div>
        <NavLink to="/dashboard" onClick={onClose} className={({isActive})=>navClass(isActive)}><LayoutDashboard size={16} className="text-[#9E7D3B]"/><span>Dashboard</span></NavLink>
        <div className={'rk-workspace-group mt-2 mb-2 rounded-md border '+(inWorkspace?'border-[#C9A67D] bg-[#F7F1E8]':'border-[#E5E0D8] bg-[#F8F5F0]')}>
          <button type="button" onClick={()=>setExpanded(v=>!v)} aria-expanded={expanded} aria-controls="rk-workspace-links" className="rk-workspace-toggle w-full flex items-center gap-2 px-3 py-2.5 text-left text-xs font-semibold tracking-wide text-[#42372D]">
            <BriefcaseBusiness size={17} className="text-[#9E7D3B]"/><span className="flex-1">WORKSPACE</span><ChevronDown size={15} className={'transition-transform '+(expanded?'':'-rotate-90')}/>
          </button>
          {expanded && <div id="rk-workspace-links" className="px-2 pb-2 space-y-0.5">
            {workspace.map(item => <NavLink key={item.path} to={item.path} onClick={onClose} className={({isActive})=>navClass(isActive)+' rk-workspace-item rounded-md pl-4'}><item.icon size={16} className="text-[#9E7D3B]"/><span>{item.name}</span></NavLink>)}
          </div>}
        </div>
        {main.filter(item=>item.path!=='/dashboard').map(item=><NavLink key={item.path} to={item.path} onClick={onClose} className={({isActive})=>navClass(isActive)}><item.icon size={16} className="text-[#9E7D3B]"/><span>{item.name}</span></NavLink>)}
      </nav>
      <div className="p-4 mx-4 mb-4 border border-[#E5E0D8] bg-[#FFFFFF]"><div className="flex items-center gap-2 text-[#9E7D3B] text-xs font-serif font-semibold mb-1"><Sparkles size={13}/><span>Winter Season '26</span></div><p className="text-[11px] text-[#736F68] leading-relaxed">High destination wedding intake active across Rajasthan heritage properties.</p></div>
      <div className="p-4 border-t border-[#E5E0D8] bg-[#FFFFFF]"><button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 px-3 py-2.5 text-xs uppercase tracking-wider text-[#736F68] hover:text-[#1F2421] hover:bg-[#F5F2EB] border border-[#E5E0D8] transition-colors"><LogOut size={14}/><span>Sign Out</span></button></div>
    </aside>
  </>;
};
