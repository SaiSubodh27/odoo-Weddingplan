import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import { Mail, Lock, Eye, EyeOff, ArrowRight, ShieldCheck, Check, Sparkles } from 'lucide-react';
import './LoginPage.css';

function Lotus() {
  return <svg viewBox="0 0 64 40" className="lovable-lotus" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden="true">
    <path d="M32 4c-6 8-6 20 0 30 6-10 6-22 0-30Z" />
    <path d="M32 34c-4-9-12-15-20-16 1 9 9 16 20 16Z" />
    <path d="M32 34c4-9 12-15 20-16-1 9-9 16-20 16Z" />
    <path d="M32 34C24 30 12 28 4 30c6 4 16 6 28 4Z" />
    <path d="M32 34c8-4 20-6 28-4-6 4-16 6-28 4Z" />
  </svg>;
}

const DEMO_PERSONAS = [
  {
    roleKey: 'staff',
    label: 'Planner',
    title: 'Principal Planner',
    email: 'planner@theroyalknot.in',
    name: 'Maharani Gayatri Singh',
    desc: 'Agency dashboard, projects, enquiries, tasks & calendar'
  },
  {
    roleKey: 'founder',
    label: 'Founder',
    title: 'Managing Director',
    email: 'founder@theroyalknot.com',
    name: 'Vikramaditya Rathore',
    desc: 'Executive profitability, margins & loss-prevention audits'
  },
  {
    roleKey: 'client',
    label: 'Client',
    title: 'Royal Couple',
    email: 'aarav.meera@heritage-singhania.com',
    name: 'Aarav & Meera',
    desc: 'Client celebration suite, details intake & OTP agreement'
  },
  {
    roleKey: 'vendor',
    label: 'Vendor',
    title: 'Luxury Florals',
    email: 'vendor@theroyalknot.com',
    name: 'Rajwada Floral Couture',
    desc: 'Quotation RFQs, schedule RSVP & business storefront'
  }
];

export const LoginPage: React.FC = () => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [accountType, setAccountType] = useState<'User' | 'Employee' | 'Vendor'>('User');
  const [signupMethod, setSignupMethod] = useState<'email' | 'phone'>('email');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [signupNotice, setSignupNotice] = useState('');
  const [email, setEmail] = useState('planner@theroyalknot.in');
  const [password, setPassword] = useState('RoyalKnot2026!');
  const [selectedPersona, setSelectedPersona] = useState<string>('staff');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [isSigningUp, setIsSigningUp] = useState(false);
  const [show, setShow] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useClients();
  const navigate = useNavigate();

  const handleSelectPersona = (p: typeof DEMO_PERSONAS[0]) => {
    setSelectedPersona(p.roleKey);
    setEmail(p.email);
    setPassword('RoyalKnot2026!');
    setError('');
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      setSignupNotice('Please enter your full name.');
      return;
    }
    const finalEmail = signupMethod === 'email' ? signupEmail.trim() : `user_${phone.replace(/\D/g, '')}@theroyalknot.in`;
    if (!finalEmail) {
      setSignupNotice('Please provide a valid email or phone number.');
      return;
    }
    setIsSigningUp(true);
    setSignupNotice('');
    try {
      const role = accountType === 'User' ? 'client' : accountType === 'Employee' ? 'staff' : 'vendor';
      const res = await authApi.signup({
        fullName: fullName.trim(),
        email: finalEmail,
        phone: signupMethod === 'phone' ? phone.trim() : undefined,
        password: signupPassword,
        role
      });

      const isClient = res.role === 'client';
      const isFounder = res.role === 'founder';
      const isVendor = res.role === 'vendor';
      const hasCompletedDetails = res.hasCompletedDetails ?? res.has_completed_details ?? (!isClient);
      const hasSigned = res.hasSignedAgreement ?? res.has_signed_agreement ?? (!isClient);

      const roleLabel = isClient
        ? 'Client Workspace'
        : isFounder
        ? 'Agency Founder'
        : isVendor
        ? 'Vendor Partner'
        : 'Principal Wedding Planner';

      login(res.email, {
        name: res.clientName || res.client_name || fullName,
        role: roleLabel,
        clientId: res.clientId || res.client_id,
        hasCompletedDetails,
        hasSignedAgreement: hasSigned,
        agreementId: res.agreementId || res.agreement_id,
        token: res.accessToken || res.access_token
      });

      if (isClient) {
        if (!hasCompletedDetails) {
          navigate('/client-intake');
        } else if (!hasSigned) {
          navigate('/agreement');
        } else {
          navigate('/client-portal');
        }
      } else if (isFounder) {
        navigate('/founder-portal');
      } else if (isVendor) {
        navigate('/vendor-portal');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setSignupNotice(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSigningUp(false);
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
      const res = await authApi.login({ email, password });
      const isClient = res.role === 'client';
      const isFounder = res.role === 'founder';
      const isVendor = res.role === 'vendor';
      const hasCompletedDetails = res.hasCompletedDetails ?? res.has_completed_details ?? (!isClient);
      const hasSigned = res.hasSignedAgreement ?? res.has_signed_agreement ?? (!isClient);

      const roleLabel = isClient
        ? 'Client Workspace'
        : isFounder
        ? 'Agency Founder'
        : isVendor
        ? 'Vendor Partner'
        : 'Principal Wedding Planner';

      login(res.email, {
        name: res.clientName || res.client_name,
        role: roleLabel,
        clientId: res.clientId || res.client_id,
        hasCompletedDetails,
        hasSignedAgreement: hasSigned,
        agreementId: res.agreementId || res.agreement_id,
        token: res.accessToken || res.access_token
      });

      if (isClient) {
        if (!hasCompletedDetails) {
          navigate('/client-intake');
        } else if (!hasSigned) {
          navigate('/agreement');
        } else {
          navigate('/client-portal');
        }
      } else if (isFounder) {
        navigate('/founder-portal');
      } else if (isVendor) {
        navigate('/vendor-portal');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
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

  const activePersonaObj = DEMO_PERSONAS.find(p => p.roleKey === selectedPersona);

  return (
    <main className="lovable-login">
      <div className="lovable-overlay" aria-hidden="true" />
      <section aria-labelledby="brand" className="lovable-card">
        <p className="lovable-eyebrow">✦ AGENCY AND CLIENT PORTAL ✦</p>
        <div className="lovable-lotus-row"><Lotus /></div>
        <h1 id="brand">THE <span>ROYAL</span> KNOT</h1>
        <p className="lovable-subtitle">WEDDING MANAGEMENT</p>
        <div className="lovable-divider" aria-hidden="true"><i />◆<i /></div>

        <div className="lovable-auth-switch" role="tablist" aria-label="Account access">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={mode === 'login' ? 'active' : ''}
            onClick={() => { setMode('login'); setSignupNotice(''); }}
          >
            Sign in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'signup'}
            className={mode === 'signup' ? 'active' : ''}
            onClick={() => { setMode('signup'); setSignupNotice(''); }}
          >
            Sign up
          </button>
        </div>

        {mode === 'login' && (
          <div className="my-3 p-3 bg-[#FBF8F3] border border-[#E9DFD0] rounded-xl text-left">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-[#9E7D3B] flex items-center gap-1">
                <Sparkles size={11} /> 4 Demo Personas (1-Click Switch)
              </span>
              <span className="text-[10px] text-[#8C8276] font-mono">Password: RoyalKnot2026!</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {DEMO_PERSONAS.map(p => (
                <button
                  key={p.roleKey}
                  type="button"
                  onClick={() => handleSelectPersona(p)}
                  className={`px-2 py-1.5 text-[11px] rounded font-medium border text-center transition-all ${
                    selectedPersona === p.roleKey
                      ? 'bg-[#1F2421] text-[#FAF8F5] border-[#1F2421] shadow-sm font-semibold'
                      : 'bg-white text-[#5C5349] border-[#DED6CA] hover:bg-[#F2ECE1]'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
            {activePersonaObj && (
              <p className="text-[11px] text-[#7A6F62] mt-2 italic">
                <b>{activePersonaObj.name}:</b> {activePersonaObj.desc}
              </p>
            )}
          </div>
        )}

        {mode === 'signup' ? (
          <div className="lovable-signup">
            <p className="lovable-signup-label">I AM JOINING AS</p>
            <div className="lovable-role-picker">
              {(['User', 'Employee', 'Vendor'] as const).map(role => (
                <button
                  key={role}
                  type="button"
                  className={accountType === role ? 'selected' : ''}
                  onClick={() => { setAccountType(role); setSignupNotice(''); }}
                >
                  {role}
                </button>
              ))}
            </div>
            <p className="lovable-signup-help">
              {accountType === 'User'
                ? 'Create an account to manage your wedding experience.'
                : accountType === 'Employee'
                ? 'Employee accounts require approval from your agency administrator.'
                : 'Vendor accounts require verification before portal access.'}
            </p>
            <div className="lovable-role-picker lovable-method-picker">
              <button
                type="button"
                className={signupMethod === 'email' ? 'selected' : ''}
                onClick={() => setSignupMethod('email')}
              >
                Email
              </button>
              <button
                type="button"
                className={signupMethod === 'phone' ? 'selected' : ''}
                onClick={() => setSignupMethod('phone')}
              >
                Phone number
              </button>
            </div>
            <form className="lovable-form lovable-signup-form" onSubmit={handleSignup}>
              <div>
                <label htmlFor="signup-name">FULL NAME</label>
                <div className="lovable-input">
                  <input
                    id="signup-name"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="Your full name"
                    required
                  />
                </div>
              </div>
              {signupMethod === 'email' ? (
                <div>
                  <label htmlFor="signup-email">EMAIL ADDRESS</label>
                  <div className="lovable-input">
                    <Mail size={16} />
                    <input
                      id="signup-email"
                      type="email"
                      value={signupEmail}
                      onChange={e => setSignupEmail(e.target.value)}
                      placeholder="name@example.com"
                      required
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label htmlFor="signup-phone">PHONE NUMBER</label>
                  <div className="lovable-input">
                    <input
                      id="signup-phone"
                      type="tel"
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="+91 98765 43210"
                      required
                    />
                  </div>
                </div>
              )}
              <div>
                <label htmlFor="signup-password">CONFIDENTIAL PASSWORD</label>
                <div className="lovable-input">
                  <Lock size={16} />
                  <input
                    id="signup-password"
                    type={showSignupPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={signupPassword}
                    onChange={e => setSignupPassword(e.target.value)}
                    placeholder="Create your own password"
                    minLength={6}
                    required
                  />
                  <button
                    type="button"
                    aria-label={showSignupPassword ? "Hide password" : "Show password"}
                    aria-pressed={showSignupPassword}
                    onClick={() => setShowSignupPassword(!showSignupPassword)}
                  >
                    {showSignupPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <button className="lovable-submit" type="submit" disabled={isSigningUp}>
                {isSigningUp ? 'CREATING ACCOUNT…' : 'CREATE ACCOUNT'} <ArrowRight size={16} />
              </button>
            </form>
            {signupNotice && <p role="status" className="lovable-signup-notice">{signupNotice}</p>}
            <p className="lovable-signup-foot">Secure registration and account creation connected to The Royal Knot heritage portal.</p>
          </div>
        ) : (
          <form onSubmit={handleLogin} className="lovable-form">
            {error && <p role="alert" className="lovable-error">{error}</p>}
            <div>
              <label htmlFor="email">EMAIL ADDRESS</label>
              <div className="lovable-input">
                <Mail size={16} />
                <input
                  id="email"
                  type="email"
                  autoComplete="username"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setSelectedPersona(''); }}
                  placeholder="planner@theroyalknot.in"
                  required
                />
              </div>
            </div>
            <div>
              <div className="lovable-label-row">
                <label htmlFor="password">PASSWORD</label>
                <button type="button" onClick={() => alert('Default demo password for all accounts is RoyalKnot2026!')}>
                  Forgot password?
                </button>
              </div>
              <div className="lovable-input">
                <Lock size={16} />
                <input
                  id="password"
                  type={show ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  aria-label={show ? 'Hide password' : 'Show password'}
                  onClick={() => setShow(!show)}
                >
                  {show ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <label className="lovable-remember">
              <input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} />
              <span className="lovable-checkbox">{rememberMe && <Check size={12} strokeWidth={3} />}</span>
              Remember this terminal
            </label>
            <button className="lovable-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'VERIFYING…' : 'ENTER AGENCY SYSTEM'}
              <ArrowRight size={16} />
            </button>
          </form>
        )}
        <p className="lovable-authorized"><ShieldCheck size={16} />Secure access for authorised agency staff and registered clients</p>
      </section>
      <footer className="lovable-footer">JAIPUR OFFICE: RAMBAGH ENCLAVE <span>|</span> UDAIPUR OFFICE: PICHOLA PROMENADE</footer>
    </main>
  );
};
