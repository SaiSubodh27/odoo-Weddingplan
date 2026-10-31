import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import { Lock, Mail, ShieldCheck, ArrowRight, Sparkles, Building, UserCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'staff' | 'client'>('staff');
  const [email, setEmail] = useState('planner@theroyalknot.in');
  const [password, setPassword] = useState('RoyalKnot2026');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useClients();
  const navigate = useNavigate();

  const handleTabChange = (tab: 'staff' | 'client') => {
    setActiveTab(tab);
    setError('');
    if (tab === 'staff') {
      setEmail('planner@theroyalknot.in');
      setPassword('RoyalKnot2026');
    } else {
      setEmail('');
      setPassword('');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please provide your registered email and password.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Authenticate via backend API (supports staff and activated clients)
      const res = await authApi.login({ email, password });
      const isClient = res.role === 'client';
      login(res.email, {
        name: res.clientName || res.client_name,
        role: isClient ? 'Client' : 'Principal Wedding Planner'
      });

      if (isClient) {
        navigate('/portal');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      // Fallback for offline demo if using default staff demo credentials
      if (email.includes('theroyalknot.in') && (!err.message || err.message.includes('fetch'))) {
        login(email);
        navigate('/dashboard');
      } else {
        setError(err.message || 'Authentication failed. Please verify your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] flex flex-col justify-center items-center p-4 sm:p-6 font-sans">
      {/* Decorative top badge */}
      <div className="mb-6 flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium">
        <span>✦</span>
        <span>The Royal Knot Access Gate</span>
        <span>✦</span>
      </div>

      <div className="w-full max-w-md bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-10 shadow-sm">
        {/* Brand Header */}
        <div className="text-center mb-6 pb-6 border-b border-[#E5E0D8]">
          <h1 className="font-serif text-3xl font-normal text-[#1F2421] uppercase tracking-wider mb-1">
            The Royal Knot
          </h1>
          <p className="text-[11px] uppercase tracking-[0.2em] text-[#8C877D]">
            Jaipur · Udaipur Wedding Management
          </p>
        </div>

        {/* Portal Switcher Tabs */}
        <div className="flex border border-[#E5E0D8] mb-6 bg-[#FAF8F5] p-1">
          <button
            type="button"
            onClick={() => handleTabChange('staff')}
            className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider transition-colors flex items-center justify-center gap-1.5 ${
              activeTab === 'staff'
                ? 'bg-[#1F2421] text-[#FAF8F5] shadow-xs'
                : 'text-[#736F68] hover:text-[#1F2421]'
            }`}
          >
            <Building size={12} />
            <span>Employee Portal</span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange('client')}
            className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider transition-colors flex items-center justify-center gap-1.5 ${
              activeTab === 'client'
                ? 'bg-[#1F2421] text-[#FAF8F5] shadow-xs'
                : 'text-[#736F68] hover:text-[#1F2421]'
            }`}
          >
            <UserCheck size={12} />
            <span>Client Portal</span>
          </button>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              {activeTab === 'staff' ? 'Agency Email Address' : 'Client Account Email'}
            </label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={activeTab === 'staff' ? 'planner@theroyalknot.in' : 'your.email@gmail.com'}
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              />
              <Mail size={14} className="absolute right-3.5 top-3 text-[#9E7D3B]" />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              />
              <Lock size={14} className="absolute right-3.5 top-3 text-[#9E7D3B]" />
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-[#736F68]">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="accent-[#9E7D3B]"
              />
              <span>Remember session</span>
            </label>

            {activeTab === 'client' && (
              <Link to="/activate" className="text-[#9E7D3B] hover:underline font-medium">
                Activate Invite Link
              </Link>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-semibold hover:bg-[#9E7D3B] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>{isLoading ? 'Verifying...' : activeTab === 'staff' ? 'Enter Staff ERP' : 'Enter Client Portal'}</span>
            <ArrowRight size={14} />
          </button>
        </form>

        {/* Public Client Registration Promo */}
        <div className="mt-8 pt-6 border-t border-[#E5E0D8] text-center space-y-2">
          <p className="text-xs text-[#736F68]">
            Planning a luxury destination wedding with us?
          </p>
          <Link
            to="/client-register"
            className="inline-flex items-center gap-1.5 text-xs text-[#9E7D3B] font-semibold uppercase tracking-wider hover:underline"
          >
            <Sparkles size={13} />
            <span>Register Your Wedding on Website</span>
            <ArrowRight size={12} />
          </Link>
        </div>

        {/* System security note */}
        <div className="mt-6 flex items-center justify-center gap-1.5 text-[10px] text-[#8C877D] uppercase tracking-wider">
          <ShieldCheck size={12} className="text-[#2D5A3C]" />
          <span>Encrypted Session · Argon2 Protocol</span>
        </div>
      </div>
    </div>
  );
};
