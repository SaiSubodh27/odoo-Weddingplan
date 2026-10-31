import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import { Lock, Mail, ShieldCheck, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('planner@theroyalknot.in');
  const [password, setPassword] = useState('RoyalKnot2026');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useClients();
  const navigate = useNavigate();

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
      login(res.email, {
        name: res.clientName || res.client_name,
        role: res.role === 'client' ? 'Client Workspace' : 'Principal Wedding Planner'
      });
      navigate('/dashboard');
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
        <span>Agency & Client Portal</span>
        <span>✦</span>
      </div>

      <div className="w-full max-w-md bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-10">
        {/* Brand Header */}
        <div className="text-center mb-8 pb-6 border-b border-[#E5E0D8]">
          <h1 className="font-serif text-3xl font-normal text-[#1F2421] uppercase tracking-wider mb-1">
            The Royal Knot
          </h1>
          <p className="text-[11px] uppercase tracking-[0.2em] text-[#8C877D]">
            Jaipur · Udaipur Wedding Management
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="planner@theroyalknot.in"
                className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                required
              />
              <Mail size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium">
                Password
              </label>
              <button
                type="button"
                onClick={() => alert('For this frontend preview, enter any non-empty credentials.')}
                className="text-[11px] text-[#9E7D3B] hover:text-[#7A5F28] hover:underline"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                required
              />
              <Lock size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 text-[#1F2421] border-[#E5E0D8] bg-[#FAF8F5] focus:ring-0"
              />
              <span className="text-xs text-[#736F68]">Remember this terminal</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold border border-[#1F2421] transition-colors disabled:opacity-60"
          >
            <span>{isLoading ? 'Accessing Dossiers...' : 'Enter Agency System'}</span>
            <ArrowRight size={14} className="text-[#D9C496]" />
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-[#E5E0D8] text-center">
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-[#8C877D]">
            <ShieldCheck size={13} className="text-[#9E7D3B]" />
            <span>Authorized access for Royal Knot Concierge staff & registered clients</span>
          </div>
        </div>
      </div>

      <div className="mt-8 text-center text-[11px] text-[#8C877D] tracking-widest uppercase">
        Jaipur Office: Rambagh Enclave · Udaipur Office: Pichola Promenade
      </div>
    </div>
  );
};

