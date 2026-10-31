import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { Lock, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, KeyRound } from 'lucide-react';

export const ClientActivationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [isVerifying, setIsVerifying] = useState(true);
  const [tokenInfo, setTokenInfo] = useState<{
    valid: boolean;
    email?: string;
    clientName?: string;
    message?: string;
  } | null>(null);

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activatedSuccess, setActivatedSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setIsVerifying(false);
      setTokenInfo({
        valid: false,
        message: 'No activation token was provided in the link. Please verify your invitation email.'
      });
      return;
    }

    const verify = async () => {
      try {
        const res = await authApi.verifyToken(token);
        setTokenInfo({
          valid: res.valid,
          email: res.email,
          clientName: res.clientName || res.client_name,
          message: res.message
        });
      } catch (err: any) {
        setTokenInfo({
          valid: false,
          message: err.message || 'Unable to verify activation link with the server.'
        });
      } finally {
        setIsVerifying(false);
      }
    };

    verify();
  }, [token]);

  const handleActivation = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please ensure both fields are identical.');
      return;
    }

    setIsSubmitting(true);

    try {
      await authApi.activate({
        token,
        password,
        confirmPassword,
      });
      setActivatedSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Account activation failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] flex flex-col justify-center items-center p-4 sm:p-6 font-sans">
      {/* Decorative top badge */}
      <div className="mb-6 flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-[#9E7D3B] font-medium">
        <span>✦</span>
        <span>The Royal Knot Concierge</span>
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

        {/* State 1: Verifying Token */}
        {isVerifying && (
          <div className="py-12 text-center space-y-4">
            <div className="w-10 h-10 border-2 border-[#9E7D3B] border-t-transparent animate-spin mx-auto" />
            <p className="text-xs uppercase tracking-widest text-[#736F68]">
              Validating Invitation Token...
            </p>
          </div>
        )}

        {/* State 2: Invalid or Expired Token */}
        {!isVerifying && (!tokenInfo || !tokenInfo.valid) && (
          <div className="space-y-6">
            <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs flex gap-3">
              <AlertCircle size={18} className="shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold uppercase tracking-wider mb-1">Activation Link Expired or Invalid</p>
                <p className="text-[11px] text-[#7A2E27] leading-relaxed">
                  {tokenInfo?.message || 'This activation link cannot be used. It may have expired (links are valid for 72 hours) or was already activated.'}
                </p>
              </div>
            </div>

            <p className="text-xs text-[#736F68] leading-relaxed">
              If your link has expired, please contact your wedding concierge at The Royal Knot to request a fresh activation link.
            </p>

            <div className="pt-2">
              <Link
                to="/login"
                className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold border border-[#1F2421] transition-colors"
              >
                <span>Return to Portal Login</span>
                <ArrowRight size={14} className="text-[#D9C496]" />
              </Link>
            </div>
          </div>
        )}

        {/* State 3: Successfully Activated */}
        {!isVerifying && activatedSuccess && (
          <div className="space-y-6">
            <div className="p-4 bg-[#F2F7F2] border border-[#CDE3CD] text-[#245928] text-xs flex gap-3">
              <CheckCircle2 size={18} className="shrink-0 mt-0.5 text-[#245928]" />
              <div>
                <p className="font-semibold uppercase tracking-wider mb-1">Account Activated</p>
                <p className="text-[11px] text-[#245928] leading-relaxed">
                  Your client account is now secure and active. You can now log in to review your wedding dossier and arrangements.
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate('/login')}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold border border-[#1F2421] transition-colors"
            >
              <span>Proceed to Login</span>
              <ArrowRight size={14} className="text-[#D9C496]" />
            </button>
          </div>
        )}

        {/* State 4: Valid Token - Password Form */}
        {!isVerifying && tokenInfo && tokenInfo.valid && !activatedSuccess && (
          <form onSubmit={handleActivation} className="space-y-5">
            <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-4 text-xs">
              <div className="text-[10px] uppercase tracking-wider text-[#9E7D3B] font-semibold mb-1">
                Client Registration Confirmed
              </div>
              <div className="font-serif text-sm font-medium text-[#1F2421]">
                {tokenInfo.clientName || 'Valued Client'}
              </div>
              <div className="text-[11px] text-[#736F68] mt-0.5">
                {tokenInfo.email}
              </div>
            </div>

            <p className="text-xs text-[#736F68] leading-relaxed">
              Please choose a private password to activate your Royal Knot account and access your wedding planning workspace.
            </p>

            {error && (
              <div className="p-3 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                New Password (minimum 8 characters)
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                  required
                  minLength={8}
                />
                <Lock size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
              </div>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                  required
                  minLength={8}
                />
                <KeyRound size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold border border-[#1F2421] transition-colors disabled:opacity-60"
              >
                <span>{isSubmitting ? 'Securing Account...' : 'Activate Client Account'}</span>
                <ArrowRight size={14} className="text-[#D9C496]" />
              </button>
            </div>
          </form>
        )}

        <div className="mt-8 pt-6 border-t border-[#E5E0D8] text-center">
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-[#8C877D]">
            <ShieldCheck size={13} className="text-[#9E7D3B]" />
            <span>Encrypted with Argon2 cryptographic verification</span>
          </div>
        </div>
      </div>

      <div className="mt-8 text-center text-[11px] text-[#8C877D] tracking-widest uppercase">
        The Royal Knot · Jaipur and Udaipur Destination Wedding Agency
      </div>
    </div>
  );
};
