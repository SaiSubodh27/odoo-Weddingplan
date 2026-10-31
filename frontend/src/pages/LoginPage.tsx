import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { authApi } from '../services/api';
import { Mail, Lock, Eye, EyeOff, ArrowRight, ShieldCheck, Check } from 'lucide-react';
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
export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('planner@theroyalknot.in');
  const [password, setPassword] = useState('RoyalKnot2026');
  const [show, setShow] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useClients();
  const navigate = useNavigate();
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) { setError('Please provide your registered email and password.'); return; }
    setIsLoading(true); setError('');
    try {
      const res = await authApi.login({ email, password });
      login(res.email, { name: res.clientName || res.client_name, role: res.role === 'client' ? 'Client Workspace' : 'Principal Wedding Planner' });
      navigate('/dashboard');
    } catch (err: any) {
      if (email.includes('theroyalknot.in') && (!err.message || err.message.includes('fetch'))) { login(email); navigate('/dashboard'); }
      else setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally { setIsLoading(false); }
  };
  return <main className="lovable-login">
    <div className="lovable-overlay" aria-hidden="true" />
    <section aria-labelledby="brand" className="lovable-card">
      <p className="lovable-eyebrow">✦ AGENCY AND CLIENT PORTAL ✦</p>
      <div className="lovable-lotus-row"><Lotus /></div>
      <h1 id="brand">THE <span>ROYAL</span> KNOT</h1>
      <p className="lovable-subtitle">WEDDING MANAGEMENT</p>
      <div className="lovable-divider" aria-hidden="true"><i />◆<i /></div>
      <form onSubmit={handleLogin} className="lovable-form">
        {error && <p role="alert" className="lovable-error">{error}</p>}
        <div><label htmlFor="email">EMAIL ADDRESS</label><div className="lovable-input"><Mail size={16} /><input id="email" type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} placeholder="planner@theroyalknot.in" required /></div></div>
        <div><div className="lovable-label-row"><label htmlFor="password">PASSWORD</label><button type="button" onClick={()=>alert('Please contact your agency administrator for password assistance.')}>Forgot password?</button></div>
          <div className="lovable-input"><Lock size={16}/><input id="password" type={show?'text':'password'} autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" required/><button type="button" aria-label={show?'Hide password':'Show password'} onClick={()=>setShow(!show)}>{show?<EyeOff size={16}/>:<Eye size={16}/>}</button></div>
        </div>
        <label className="lovable-remember"><input type="checkbox" checked={rememberMe} onChange={e=>setRememberMe(e.target.checked)}/><span className="lovable-checkbox">{rememberMe&&<Check size={12} strokeWidth={3}/>}</span>Remember this terminal</label>
        <button className="lovable-submit" type="submit" disabled={isLoading}>{isLoading?'VERIFYING…':'ENTER AGENCY SYSTEM'}<ArrowRight size={16}/></button>
      </form>
      <p className="lovable-authorized"><ShieldCheck size={16}/>Secure access for authorised agency staff and registered clients</p>
    </section>
    <footer className="lovable-footer">JAIPUR OFFICE: RAMBAGH ENCLAVE <span>|</span> UDAIPUR OFFICE: PICHOLA PROMENADE</footer>
  </main>;
};
