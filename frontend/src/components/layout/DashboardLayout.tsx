import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const dashboard = location.pathname === '/dashboard';
  return (
    <div className={'min-h-screen bg-[#FAF8F5] text-[#1F2421] flex flex-col font-sans' + (dashboard ? ' rk-dashboard-shell' : '')}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
        <Topbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto"><Outlet /></main>
        <footer className="py-4 px-6 border-t border-[#E5E0D8] bg-[#FFFFFF] text-center text-[11px] text-[#8C877D] uppercase tracking-widest">
          The Royal Knot — Bespoke Royal Weddings · Jaipur and Udaipur Operating System
        </footer>
      </div>
    </div>
  );
};
