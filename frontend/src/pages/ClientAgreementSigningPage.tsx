import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../context/ClientContext';
import { agreementApi } from '../services/api';
import { 
  CheckCircle2, 
  ArrowRight, 
  Download, 
  AlertCircle, 
  Clock, 
  Sparkles,
  Lock,
  Eraser
} from 'lucide-react';

interface AgreementData {
  id: string;
  agreement_number: string;
  client_id: string;
  client_name?: string;
  client_email?: string;
  client_phone?: string;
  status: string;
  wedding_date: string;
  wedding_location: string;
  venue?: string;
  guest_count: number;
  service_package: string;
  included_services?: string[];
  deliverables?: string[];
  package_price: number | string;
  tax_percentage: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  currency: string;
  agreement_version: string;
  is_verified: boolean;
  signed_at?: string;
  signed_by_name?: string;
  signed_pdf_url?: string;
  signing_otp_verified?: boolean;
  consent_confirmed?: boolean;
  milestones?: Array<{
    id: string;
    sequence_order: number;
    milestone_name: string;
    percentage: number | string;
    amount: number | string;
    due_description: string;
    status: string;
  }>;
}

export const ClientAgreementSigningPage: React.FC = () => {
  const { currentUser, setHasSignedAgreement, setAgreementId } = useClients();
  const navigate = useNavigate();

  const [agreement, setAgreement] = useState<AgreementData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // OTP state
  const [otpSent, setOtpSent] = useState<boolean>(false);
  const [otpCode, setOtpCode] = useState<string>('');
  const [otpSending, setOtpSending] = useState<boolean>(false);
  const [otpVerifying, setOtpVerifying] = useState<boolean>(false);
  const [otpVerified, setOtpVerified] = useState<boolean>(false);
  const [otpMessage, setOtpMessage] = useState<string>('');
  const [otpError, setOtpError] = useState<string>('');

  // Signature state
  const [signerName, setSignerName] = useState<string>('');
  const [consentChecked, setConsentChecked] = useState<boolean>(false);
  const [signing, setSigning] = useState<boolean>(false);
  const [hasDrawnSignature, setHasDrawnSignature] = useState<boolean>(false);

  // Canvas
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDrawing = useRef<boolean>(false);

  useEffect(() => {
    fetchAgreement();
  }, []);

  const fetchAgreement = async () => {
    setLoading(true);
    setError('');
    try {
      const targetClientId = currentUser.clientId || localStorage.getItem('the_royal_knot_client_id_v1') || undefined;
      const data = await agreementApi.getMyAgreement(targetClientId);
      setAgreement(data);
      setAgreementId(data.id);
      if (data.client_name) setSignerName(data.client_name);
      if (data.status === 'SIGNED' || data.is_verified) {
        setHasSignedAgreement(true);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load service agreement.');
    } finally {
      setLoading(false);
    }
  };

  // Canvas drawing functions
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    isDrawing.current = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#1F2421';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    setHasDrawnSignature(true);
  };

  const stopDrawing = () => {
    isDrawing.current = false;
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawnSignature(false);
  };

  // OTP Handlers
  const handleSendOtp = async () => {
    if (!agreement) return;
    setOtpSending(true);
    setOtpError('');
    setOtpMessage('');
    try {
      const res = await agreementApi.sendOtp(agreement.id);
      setOtpSent(true);
      setOtpCode('');
      setOtpMessage(`Verification code sent to ${res.email_destination || agreement.client_email}. Code valid for 10 minutes.`);
    } catch (err: any) {
      setOtpError(err.message || 'Failed to send verification code.');
    } finally {
      setOtpSending(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!agreement || !otpCode.trim()) return;
    setOtpVerifying(true);
    setOtpError('');
    try {
      const res = await agreementApi.verifyOtp(agreement.id, otpCode.trim());
      if (res.verified) {
        setOtpVerified(true);
        setOtpMessage('✓ Identity successfully verified via email code.');
      }
    } catch (err: any) {
      setOtpError(err.message || 'Invalid or expired code.');
    } finally {
      setOtpVerifying(false);
    }
  };

  // Signature submission
  const handleSignAgreement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreement) return;

    if (!otpVerified) {
      setOtpError('Please verify your email code before signing.');
      return;
    }

    if (!hasDrawnSignature) {
      setError('Please provide your digital signature on the canvas below.');
      return;
    }

    if (!consentChecked) {
      setError('You must explicitly consent to the contract terms before submitting.');
      return;
    }

    const canvas = canvasRef.current;
    const signatureData = canvas ? canvas.toDataURL('image/png') : 'DIGITAL_SIGNATURE_CONFIRMED';

    setSigning(true);
    setError('');

    try {
      const res = await agreementApi.signAgreement(agreement.id, {
        otp: otpCode.trim(),
        signature_data: signatureData,
        consent: true,
        signer_name: signerName.trim() || agreement.client_name || 'Client'
      });

      setHasSignedAgreement(true);
      setAgreement(prev => prev ? { ...prev, status: 'SIGNED', is_verified: true, signed_at: res.signed_at } : null);

      // Automatically advance to dashboard upon successful execution
      setTimeout(() => {
        navigate('/client-portal');
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to execute digital signature.');
    } finally {
      setSigning(false);
    }
  };

  const formatCurrency = (val?: number | string) => {
    if (val === undefined || val === null) return '₹0.00';
    return `₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex items-center justify-center p-6 text-[#1F2421]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-[#9E7D3B] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-serif text-lg text-[#1F2421]">Preparing Bespoke Service Agreement…</p>
          <p className="text-xs text-[#736F68] mt-1 tracking-wide">Connecting to Rajasthan Heritage Registry</p>
        </div>
      </div>
    );
  }

  if (error && !agreement) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex items-center justify-center p-6 text-[#1F2421]">
        <div className="max-w-md w-full bg-[#FFFFFF] border border-[#E5E0D8] p-8 text-center shadow-sm">
          <AlertCircle size={36} className="text-[#B85D1B] mx-auto mb-3" />
          <h2 className="font-serif text-xl mb-2">Unable to Load Agreement</h2>
          <p className="text-xs text-[#736F68] mb-6 leading-relaxed">{error}</p>
          <button
            onClick={fetchAgreement}
            className="px-6 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#333333] transition-colors"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const isSigned = agreement?.status === 'SIGNED' || agreement?.is_verified;

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#1F2421] py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* 3-Step Onboarding Roadmap Progress Bar */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 mb-6 shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-[#F2F7F2] border-l-4 border-[#2D5A3C]">
              <div className="flex items-center gap-2.5">
                <div className="w-6 h-6 rounded-full bg-[#2D5A3C] text-white flex items-center justify-center font-bold text-[11px]">
                  ✓
                </div>
                <div>
                  <p className="font-semibold text-[#2D5A3C] uppercase tracking-wider text-[11px]">Wedding Details</p>
                  <p className="text-[10px] text-[#2D5A3C] font-medium">Completed</p>
                </div>
              </div>
              {!isSigned && (
                <button
                  type="button"
                  onClick={() => navigate('/client-intake')}
                  className="text-[11px] underline text-[#9E7D3B] hover:text-[#1F2421] font-medium ml-2"
                >
                  Edit Details
                </button>
              )}
            </div>

            <div className="flex items-center gap-2.5 p-3 bg-[#FAF8F5] border-l-4 border-[#9E7D3B]">
              <div className="w-6 h-6 rounded-full bg-[#9E7D3B] text-white flex items-center justify-center font-bold text-[11px]">
                2
              </div>
              <div>
                <p className="font-semibold text-[#1F2421] uppercase tracking-wider text-[11px]">Service Agreement</p>
                <p className="text-[10px] text-[#9E7D3B] font-medium">{isSigned ? 'Signed & Ratified' : 'Active Execution'}</p>
              </div>
            </div>

            <div className={`flex items-center gap-2.5 p-3 bg-[#FFFFFF] border border-[#E5E0D8] ${isSigned ? 'border-l-4 border-[#2D5A3C] bg-[#F2F7F2]' : 'opacity-60'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] ${isSigned ? 'bg-[#2D5A3C] text-white' : 'bg-[#E5E0D8] text-[#736F68]'}`}>
                {isSigned ? '✓' : '3'}
              </div>
              <div>
                <p className={`font-semibold uppercase tracking-wider text-[11px] ${isSigned ? 'text-[#2D5A3C]' : 'text-[#736F68]'}`}>Planning Portal</p>
                <p className="text-[10px] text-[#8C877D]">{isSigned ? 'Unlocked' : 'Unlocks After Signing'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Top Header */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 mb-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E0D8] pb-6">
            <div>
              <div className="flex items-center gap-2 text-[#9E7D3B] text-[10px] uppercase font-bold tracking-[0.25em] mb-1">
                <Sparkles size={13} />
                <span>The Royal Knot · Official Service Contract</span>
              </div>
              <h1 className="font-serif text-2xl sm:text-3xl text-[#1F2421]">
                Bespoke Wedding Planning Service Agreement
              </h1>
              <p className="text-xs text-[#736F68] mt-1">
                Contract Reference: <span className="font-mono font-semibold text-[#1F2421]">{agreement?.agreement_number}</span> · Version: <span className="font-semibold text-[#1F2421]">{agreement?.agreement_version}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {isSigned ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] text-xs font-semibold uppercase tracking-wider">
                  <CheckCircle2 size={14} /> Signed & Ratified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#FDF6E2] text-[#8C6D1F] border border-[#E8D49E] text-xs font-semibold uppercase tracking-wider">
                  <Clock size={14} /> Pending Signature
                </span>
              )}
            </div>
          </div>

          {/* Banner Notice */}
          {!isSigned ? (
            <div className="mt-4 p-4 bg-[#F8F5F0] border-l-4 border-[#9E7D3B] text-xs text-[#5C5850] leading-relaxed">
              <p className="font-medium text-[#1F2421] mb-0.5">Mandatory Client Execution Required</p>
              Please review your service specifications and payment milestones below. To unlock full access to the Royal Knot wedding portal, forms, and itinerary planners, complete digital verification and signature.
            </div>
          ) : (
            <div className="mt-4 p-4 bg-[#EBF3ED] border-l-4 border-[#2D5A3C] text-xs text-[#2D5A3C] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <p className="font-semibold">Contract Legally Executed & Stored</p>
                <p className="text-[11px] opacity-90 mt-0.5">
                  Signed by {agreement?.signed_by_name} on {agreement?.signed_at ? new Date(agreement.signed_at).toLocaleString() : 'Record'}.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={`/api/v1/agreements/${agreement?.id}/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#FFFFFF] border border-[#C3D9C9] text-xs font-medium text-[#2D5A3C] hover:bg-[#F2F7F4] transition-colors"
                >
                  <Download size={13} /> Download Signed PDF
                </a>
                <button
                  onClick={() => navigate('/client-portal')}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs font-medium hover:bg-[#333333] transition-colors"
                >
                  Enter Celebration Portal <ArrowRight size={13} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Contract Content Sections */}
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-10 mb-6 shadow-sm space-y-8">
          {/* Section 1: Parties */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9E7D3B] mb-3">
              1. Parties to this Agreement
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-[#E5E0D8] bg-[#FAF8F5] p-4 text-xs">
                <p className="font-bold text-[#1F2421] uppercase tracking-wider mb-1">Service Provider</p>
                <p className="font-semibold">The Royal Knot Wedding Planning LLC</p>
                <p className="text-[#736F68] mt-0.5">Heritage Wing, Rambagh Enclave, Jaipur, Rajasthan</p>
                <p className="text-[#736F68] mt-0.5">Contact: concierge@theroyalknot.in | +91 141 289 4000</p>
                <p className="text-[#736F68] mt-0.5">Principal: Maharani Gayatri Singh</p>
              </div>
              <div className="border border-[#E5E0D8] bg-[#FAF8F5] p-4 text-xs">
                <p className="font-bold text-[#1F2421] uppercase tracking-wider mb-1">Client / Couple</p>
                <p className="font-semibold text-sm">{agreement?.client_name || 'Distinguished Couple'}</p>
                <p className="text-[#736F68] mt-0.5">Email: {agreement?.client_email || 'client@royaltest.in'}</p>
                <p className="text-[#736F68] mt-0.5">Phone: {agreement?.client_phone || 'N/A'}</p>
                <p className="text-[#736F68] mt-0.5">Client Code: <span className="font-mono">{agreement?.client_id}</span></p>
              </div>
            </div>
          </div>

          {/* Section 2: Wedding Scope */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9E7D3B] mb-3">
              2. Wedding Scope & Parameters
            </h2>
            <div className="border border-[#E5E0D8] overflow-hidden text-xs">
              <table className="w-full text-left border-collapse">
                <tbody className="divide-y divide-[#E5E0D8]">
                  <tr className="bg-[#FAF8F5]">
                    <td className="p-3 font-semibold w-1/3 text-[#5C5850]">Wedding Date</td>
                    <td className="p-3 font-medium text-[#1F2421]">{agreement?.wedding_date}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-[#5C5850]">Destination & City</td>
                    <td className="p-3 font-medium text-[#1F2421]">{agreement?.wedding_location}</td>
                  </tr>
                  <tr className="bg-[#FAF8F5]">
                    <td className="p-3 font-semibold text-[#5C5850]">Primary Palace Venue</td>
                    <td className="p-3 font-medium text-[#1F2421]">{agreement?.venue || 'Heritage Palace Grounds'}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-[#5C5850]">Expected Guest Count</td>
                    <td className="p-3 font-medium text-[#1F2421]">{agreement?.guest_count} Distinguished Guests</td>
                  </tr>
                  <tr className="bg-[#FAF8F5]">
                    <td className="p-3 font-semibold text-[#5C5850]">Service Tier / Package</td>
                    <td className="p-3 font-medium text-[#1F2421]">{agreement?.service_package}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Scope of Services */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9E7D3B] mb-3">
              3. Scope of Services & Key Deliverables
            </h2>
            <div className="border border-[#E5E0D8] p-4 bg-[#FAF8F5] text-xs space-y-2">
              {(agreement?.included_services || [
                "Exclusive heritage palace grounds reservation and royal wedding dossier",
                "Full-scale Rajputana theme styling, bespoke floral curation, and royal pavilions",
                "Luxury catering curation, royal banquet service, and silver cloche guest dining",
                "Rajasthani folk performers, shehnai maestros, and royal welcome processions",
                "Dedicated agency wedding concierge and multi-day itinerary execution"
              ]).map((s, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-[#9E7D3B] font-bold">✦</span>
                  <span className="text-[#333333]">{s}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Commercial Terms & Payment Milestones */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9E7D3B] mb-3">
              4. Commercial Terms & Payment Milestones
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <div className="p-3 border border-[#E5E0D8] bg-[#FAF8F5] text-xs">
                <p className="text-[10px] text-[#736F68] uppercase font-semibold">Package Price (Net)</p>
                <p className="font-serif text-lg font-bold text-[#1F2421] mt-0.5">{formatCurrency(agreement?.package_price)}</p>
              </div>
              <div className="p-3 border border-[#E5E0D8] bg-[#FAF8F5] text-xs">
                <p className="text-[10px] text-[#736F68] uppercase font-semibold">Applicable GST ({agreement?.tax_percentage}%)</p>
                <p className="font-serif text-lg font-bold text-[#1F2421] mt-0.5">{formatCurrency(agreement?.tax_amount)}</p>
              </div>
              <div className="p-3 border border-[#C9A67D] bg-[#FAF2E6] text-xs">
                <p className="text-[10px] text-[#85633C] uppercase font-semibold">Total Contract Value</p>
                <p className="font-serif text-lg font-bold text-[#1F2421] mt-0.5">{formatCurrency(agreement?.total_amount)}</p>
              </div>
            </div>

            <div className="border border-[#E5E0D8] overflow-hidden text-xs">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#FAF8F5] border-b border-[#E5E0D8] text-[11px] font-semibold text-[#736F68] uppercase">
                    <th className="p-3">Seq</th>
                    <th className="p-3">Milestone</th>
                    <th className="p-3">Share</th>
                    <th className="p-3">Amount (INR)</th>
                    <th className="p-3">Due Trigger</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E0D8]">
                  {(agreement?.milestones || [
                    { id: '1', sequence_order: 1, milestone_name: 'Initial Advance Retainer', percentage: '25.00', amount: Number(agreement?.total_amount || 0) * 0.25, due_description: 'Due upon contract signing to lock calendar', status: 'PENDING' },
                    { id: '2', sequence_order: 2, milestone_name: 'Design Approval & Vendor Locks', percentage: '35.00', amount: Number(agreement?.total_amount || 0) * 0.35, due_description: 'Due 90 days prior to wedding date', status: 'PENDING' },
                    { id: '3', sequence_order: 3, milestone_name: 'Final Palace Balance', percentage: '40.00', amount: Number(agreement?.total_amount || 0) * 0.40, due_description: 'Due 30 days prior to celebration launch', status: 'PENDING' }
                  ]).map((m) => (
                    <tr key={m.id} className="hover:bg-[#FAF8F5]">
                      <td className="p-3 font-mono">{m.sequence_order}</td>
                      <td className="p-3 font-medium text-[#1F2421]">{m.milestone_name}</td>
                      <td className="p-3">{m.percentage}%</td>
                      <td className="p-3 font-semibold">{formatCurrency(m.amount)}</td>
                      <td className="p-3 text-[#736F68]">{m.due_description}</td>
                      <td className="p-3">
                        <span className="inline-block px-2 py-0.5 bg-[#FAF2E6] text-[#85633C] border border-[#D8C6AC] text-[10px] font-semibold">
                          {m.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 5: Legal Terms */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9E7D3B] mb-3">
              5. Contractual Terms, Rescheduling & Cancellation
            </h2>
            <div className="border border-[#E5E0D8] p-4 bg-[#FAF8F5] text-xs text-[#5C5850] space-y-2 max-h-48 overflow-y-auto leading-relaxed font-sans">
              <p><b>5.1 Binding Contract:</b> This Service Agreement represents the final understanding between the parties. Execution via secure digital OTP and cryptographic signature constitutes a valid and legally binding contract under the Information Technology Act, 2000.</p>
              <p><b>5.2 Non-Refundable Booking Retainer:</b> The Initial Advance Milestone secures exclusive calendar reservation, principal planner commitment, and palace holds. In the event of voluntary client cancellation, the advance fee is non-refundable.</p>
              <p><b>5.3 Rescheduling:</b> Postponement requested at least 90 calendar days prior to the wedding date is permissible without penalty, subject to agency calendar availability across Rajasthan heritage properties.</p>
              <p><b>5.4 Force Majeure:</b> Neither party shall be held liable for failure to perform due to acts of God, civil emergencies, or state-mandated heritage monument closures. Dates will be mutually renegotiated in good faith.</p>
              <p><b>5.5 Jurisdiction:</b> All disputes arising out of or in connection with this Agreement shall be subject to the exclusive jurisdiction of the competent courts in Jaipur, Rajasthan.</p>
            </div>
          </div>
        </div>

        {/* Digital Execution & OTP Verification Section */}
        {!isSigned ? (
          <form onSubmit={handleSignAgreement} className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-10 shadow-sm space-y-6">
            <div className="border-b border-[#E5E0D8] pb-4">
              <h2 className="font-serif text-xl text-[#1F2421]">Digital Execution & Identity Verification</h2>
              <p className="text-xs text-[#736F68] mt-0.5">
                Complete two-step verification using a secure one-time passcode sent to your registered email.
              </p>
            </div>

            {error && (
              <div className="p-3 bg-[#FFF3E8] border border-[#FAD3B4] text-[#B85D1B] text-xs flex items-center gap-2">
                <AlertCircle size={15} />
                <span>{error}</span>
              </div>
            )}

            {/* Step 1: OTP Email Verification */}
            <div className="border border-[#E5E0D8] bg-[#FAF8F5] p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#9E7D3B]">
                  Step 1: Identity Passcode Verification
                </span>
                {otpVerified && (
                  <span className="text-xs text-[#2D5A3C] font-semibold flex items-center gap-1">
                    <CheckCircle2 size={14} /> Code Verified
                  </span>
                )}
              </div>
              <p className="text-xs text-[#736F68] mb-4">
                We will transmit a confidential 6-digit code to <b className="text-[#1F2421]">{agreement?.client_email || currentUser.email}</b>.
              </p>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <button
                  type="button"
                  onClick={handleSendOtp}
                  disabled={otpSending || otpVerified}
                  className="px-4 py-2.5 bg-[#FAF8F5] border border-[#9E7D3B] text-[#9E7D3B] hover:bg-[#FAF2E6] text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
                >
                  {otpSending ? 'Sending Code…' : otpSent ? 'Resend Code' : 'Request Verification Code'}
                </button>

                {otpSent && !otpVerified && (
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      type="text"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="Enter 6-digit code"
                      className="px-3 py-2 bg-[#FFFFFF] border border-[#E5E0D8] text-sm font-mono tracking-widest text-center w-40 focus:outline-none focus:border-[#9E7D3B]"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyOtp}
                      disabled={otpVerifying || otpCode.length !== 6}
                      className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs font-semibold uppercase tracking-wider hover:bg-[#333333] transition-colors disabled:opacity-50"
                    >
                      {otpVerifying ? 'Verifying…' : 'Verify'}
                    </button>
                  </div>
                )}
              </div>

              {otpMessage && (
                <p className="text-xs text-[#2D5A3C] mt-3 font-medium">{otpMessage}</p>
              )}
              {otpError && (
                <p className="text-xs text-[#B85D1B] mt-3 font-medium">{otpError}</p>
              )}
            </div>

            {/* Step 2: Digital Signature Pad */}
            <div className="border border-[#E5E0D8] bg-[#FAF8F5] p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#9E7D3B]">
                  Step 2: Digital Signature
                </span>
                {hasDrawnSignature && (
                  <button
                    type="button"
                    onClick={clearCanvas}
                    className="text-xs text-[#8C877D] hover:text-[#1F2421] flex items-center gap-1"
                  >
                    <Eraser size={13} /> Clear & Redraw
                  </button>
                )}
              </div>
              <p className="text-xs text-[#736F68] mb-3">
                Sign inside the box using your mouse, trackpad, or touch device.
              </p>

              <div className="bg-[#FFFFFF] border border-[#E5E0D8] inline-block w-full">
                <canvas
                  ref={canvasRef}
                  width={600}
                  height={140}
                  onMouseDown={startDrawing}
                  onMouseMove={draw}
                  onMouseUp={stopDrawing}
                  onMouseLeave={stopDrawing}
                  onTouchStart={startDrawing}
                  onTouchMove={draw}
                  onTouchEnd={stopDrawing}
                  className="w-full h-36 cursor-crosshair touch-none"
                />
              </div>

              <div className="mt-3">
                <label className="block text-[11px] uppercase tracking-wider text-[#736F68] font-semibold mb-1">
                  Signer Full Name
                </label>
                <input
                  type="text"
                  value={signerName}
                  onChange={(e) => setSignerName(e.target.value)}
                  placeholder="e.g. Prince Vikram & Princess Ananya"
                  className="w-full sm:w-80 px-3 py-2 bg-[#FFFFFF] border border-[#E5E0D8] text-xs focus:outline-none focus:border-[#9E7D3B]"
                  required
                />
              </div>
            </div>

            {/* Step 3: Consent Checkbox */}
            <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8]">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-[#E5E0D8] text-[#9E7D3B] focus:ring-[#9E7D3B]"
                />
                <span className="text-xs text-[#5C5850] leading-relaxed">
                  I explicitly confirm that I am authorized to bind the client party and that I have read, understood, and voluntarily agree to all service specifications, payment milestones, and legal terms set forth in this Royal Knot Service Agreement under the Information Technology Act, 2000.
                </span>
              </label>
            </div>

            {/* Submit Button */}
            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                type="submit"
                disabled={signing || !otpVerified || !hasDrawnSignature || !consentChecked}
                className="px-8 py-3 bg-[#1F2421] text-[#FAF8F5] hover:bg-[#333333] text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {signing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Executing Contract…
                  </>
                ) : (
                  <>
                    <Lock size={14} /> Execute & Ratify Service Agreement
                  </>
                )}
              </button>
            </div>
          </form>
        ) : null}
      </div>
    </div>
  );
};
