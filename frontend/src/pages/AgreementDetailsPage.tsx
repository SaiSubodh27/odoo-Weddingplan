import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  Send, 
  CheckCircle, 
  FileText, 
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Calendar,
  DollarSign
} from 'lucide-react';
import { agreementApi } from '../services/api';
import { ServiceAgreement, SignatureStatusResponse } from '../types/agreement';

export const AgreementDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [agreement, setAgreement] = useState<ServiceAgreement | null>(null);
  const [sigDetails, setSigDetails] = useState<SignatureStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Verification modal state
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyDecision, setVerifyDecision] = useState<'VERIFIED' | 'REJECTED' | 'NEEDS_CORRECTION'>('VERIFIED');
  const [verifyRemarks, setVerifyRemarks] = useState('All contractual terms, Leegality eSign metadata, and staged payment schedules validated by agency executive.');

  const fetchAgreement = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await agreementApi.get(id);
      setAgreement(data);
      if (data.signing_status !== 'NOT_CREATED') {
        try {
          const sig = await agreementApi.getSignatureStatus(id);
          setSigDetails(sig);
        } catch (_) {}
      } else {
        setSigDetails(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgreement();
  }, [id]);

  const handleApprove = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionMsg(null);
    try {
      await agreementApi.approve(id, 'Maharani Gayatri Singh', 'Internal compliance check completed.');
      setActionMsg({ type: 'success', text: 'Service Agreement internally approved! Eligible for Leegality dispatch.' });
      await fetchAgreement();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Approval failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendForSignature = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionMsg(null);
    try {
      const res = await agreementApi.sendForSignature(id);
      const isReal = res.environment === 'sandbox' || res.environment === 'production';
      setActionMsg({ 
        type: 'success', 
        text: isReal
          ? `Dispatched to Real Leegality ${res.environment.toUpperCase()} API! Document ID: ${res.leegality_document_id}`
          : `Dispatched in Simulation Mock mode. Document ID: ${res.leegality_document_id}`
      });
      await fetchAgreement();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Leegality dispatch failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerificationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setActionLoading(true);
    setActionMsg(null);
    try {
      await agreementApi.verify(id, 'Maharani Gayatri Singh', verifyDecision, verifyRemarks);
      setShowVerifyModal(false);
      setActionMsg({ type: 'success', text: `Verification status updated: ${verifyDecision}` });
      await fetchAgreement();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Verification failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmBooking = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionMsg(null);
    try {
      const res = await agreementApi.confirmBooking(id, 'Maharani Gayatri Singh', 'Booking finalized. Calendar dates locked.');
      setActionMsg({ type: 'success', text: res.message });
      await fetchAgreement();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Booking confirmation failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-[#8C877D]">Loading agreement dossier...</div>;
  }

  if (!agreement) {
    return (
      <div className="p-12 text-center space-y-3">
        <p className="text-sm text-red-600">Agreement not found.</p>
        <button onClick={() => navigate('/agreements')} className="text-xs text-[#9E7D3B] underline">
          Back to Agreements
        </button>
      </div>
    );
  }

  const pdfPreviewUrl = agreementApi.getPdfUrl(agreement.id, true);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E0D8]">
        <button
          onClick={() => navigate('/agreements')}
          className="inline-flex items-center gap-1.5 text-xs uppercase tracking-widest text-[#736F68] hover:text-[#1F2421]"
        >
          <ArrowLeft size={14} /> Back to Agreements
        </button>

        <div className="flex items-center gap-2">
          <a
            href={agreementApi.getPdfUrl(agreement.id, false)}
            download
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-[#E5E0D8] text-xs font-medium text-[#1F2421] hover:bg-[#FAF8F5]"
          >
            <Download size={13} /> Download PDF
          </a>

          {!agreement.is_internally_approved && (
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#9E7D3B] hover:bg-[#86682F] text-white text-xs uppercase tracking-widest font-medium"
            >
              <CheckCircle size={13} /> Approve to Send
            </button>
          )}

          {agreement.is_internally_approved && agreement.signing_status === 'NOT_CREATED' && (
            <button
              onClick={handleSendForSignature}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white text-xs uppercase tracking-widest font-medium"
            >
              <Send size={13} /> Send for eSign (Leegality)
            </button>
          )}

          {agreement.status === 'UNDER_VERIFICATION' && (
            <button
              onClick={() => setShowVerifyModal(true)}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-700 hover:bg-indigo-800 text-white text-xs uppercase tracking-widest font-medium"
            >
              <ShieldCheck size={13} /> Review & Verify
            </button>
          )}

          {agreement.is_verified && agreement.status !== 'BOOKING_CONFIRMED' && (
            <button
              onClick={handleConfirmBooking}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-5 py-2 bg-[#1F2421] hover:bg-[#343B37] text-white text-xs uppercase tracking-widest font-medium shadow-sm"
            >
              <Sparkles size={13} /> Confirm Wedding Booking
            </button>
          )}
        </div>
      </div>

      {actionMsg && (
        <div className={`p-3 text-xs border ${actionMsg.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          {actionMsg.text}
        </div>
      )}

      {/* Header Summary */}
      <div className="bg-white border border-[#E5E0D8] p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm font-bold text-[#1F2421]">{agreement.agreement_number}</span>
              <span className="text-xs px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#8C877D] font-mono">
                Version {agreement.current_version_number}.0
              </span>
              <span className="text-xs px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] font-medium">
                {agreement.status.replace(/_/g, ' ')}
              </span>
            </div>
            <h1 className="font-serif text-2xl font-semibold text-[#1F2421] mt-2">
              {agreement.client_partner1_name} & {agreement.client_partner2_name}
            </h1>
            <p className="text-xs text-[#736F68]">
              Client Dossier: <span className="font-mono">{agreement.client_id}</span> · {agreement.client_email} · {agreement.client_phone}
            </p>
          </div>

          <div className="text-right">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block">Total Value</span>
            <span className="font-serif text-2xl font-bold text-[#1F2421]">
              ₹ {Number(agreement.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
            <span className="text-[10px] text-[#9E7D3B] block uppercase tracking-wider font-medium">
              {agreement.service_package}
            </span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: PDF Preview & Dossier Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Embedded PDF Viewer */}
        <div className="lg:col-span-7 bg-white border border-[#E5E0D8] p-4 flex flex-col space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E5E0D8]">
            <div className="flex items-center gap-2">
              <FileText size={15} className="text-[#9E7D3B]" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[#1F2421]">
                Official Agreement PDF Preview
              </span>
            </div>
            <a
              href={pdfPreviewUrl}
              target="_blank"
              rel="noreferrer"
              className="text-[11px] text-[#9E7D3B] hover:underline inline-flex items-center gap-1"
            >
              Open in New Window <ExternalLink size={11} />
            </a>
          </div>

          <div className="w-full h-[620px] bg-[#FAF8F5] border border-[#E5E0D8]">
            <iframe
              src={pdfPreviewUrl}
              title="Agreement PDF"
              className="w-full h-full"
            />
          </div>
        </div>

        {/* Right Column: Workflow Details, Milestones & Signing Audit */}
        <div className="lg:col-span-5 space-y-6">
          {/* Staged Payment Schedule */}
          <div className="bg-white border border-[#E5E0D8] p-5 space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-[#E5E0D8]">
              <DollarSign size={14} className="text-[#9E7D3B]" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#1F2421]">Staged Payment Milestones</h3>
            </div>
            <div className="space-y-2">
              {agreement.milestones.map((m, idx) => (
                <div key={idx} className="p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-xs flex items-center justify-between">
                  <div>
                    <span className="font-medium text-[#1F2421] block">{m.name}</span>
                    <span className="text-[10px] text-[#8C877D]">Due: {m.due_date}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-semibold text-[#1F2421] block">
                      ₹ {Number(m.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-[10px] text-[#8C877D] font-mono">{m.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Leegality eSignature Tracking */}
          <div className="bg-white border border-[#E5E0D8] p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <Send size={14} className="text-purple-600" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#1F2421]">Leegality eSigning Status</h3>
              </div>
              {sigDetails && (
                <span className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider border ${
                  sigDetails.environment === 'sandbox' || sigDetails.environment === 'production'
                    ? 'bg-blue-50 text-blue-800 border-blue-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}>
                  {sigDetails.environment === 'sandbox' ? 'Sandbox API' : sigDetails.environment === 'production' ? 'Production API' : 'Simulation Mock'}
                </span>
              )}
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-[#FAF8F5]">
                <span className="text-[#8C877D]">Provider Status:</span>
                <span className="font-semibold text-purple-700">{agreement.signing_status}</span>
              </div>
              {sigDetails?.leegality_document_id && (
                <div className="flex items-center justify-between py-1 border-b border-[#FAF8F5]">
                  <span className="text-[#8C877D]">Document ID:</span>
                  <span className="font-mono text-[11px] font-medium text-[#1F2421]">{sigDetails.leegality_document_id}</span>
                </div>
              )}
              {sigDetails?.signer_name && (
                <div className="flex items-center justify-between py-1 border-b border-[#FAF8F5]">
                  <span className="text-[#8C877D]">Signer:</span>
                  <span className="text-[#1F2421]">{sigDetails.signer_name}</span>
                </div>
              )}
              {sigDetails?.signing_url && agreement.signing_status !== 'COMPLETED' && (
                <div className="pt-1">
                  <a
                    href={sigDetails.signing_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-[#9E7D3B] hover:text-[#86682F] font-medium hover:underline"
                  >
                    Open Client Signing Portal <ExternalLink size={12} />
                  </a>
                </div>
              )}
              <div className="flex items-center justify-between py-1 border-b border-[#FAF8F5]">
                <span className="text-[#8C877D]">Internal Approval:</span>
                <span className={`font-medium ${agreement.is_internally_approved ? 'text-emerald-700' : 'text-amber-700'}`}>
                  {agreement.is_internally_approved ? `Approved by ${agreement.approved_by}` : 'Pending Internal Approval'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#FAF8F5]">
                <span className="text-[#8C877D]">Employee Verification:</span>
                <span className={`font-medium ${agreement.is_verified ? 'text-emerald-700' : 'text-[#8C877D]'}`}>
                  {agreement.is_verified ? `Verified (${agreement.verified_by})` : 'Awaiting Post-Sign Verification'}
                </span>
              </div>
            </div>
          </div>

          {/* Wedding Function Schedule */}
          {agreement.wedding_functions && agreement.wedding_functions.length > 0 && (
            <div className="bg-white border border-[#E5E0D8] p-5 space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-[#E5E0D8]">
                <Calendar size={14} className="text-[#9E7D3B]" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#1F2421]">Ceremonies & Events</h3>
              </div>
              <div className="space-y-2">
                {agreement.wedding_functions.map((fn, idx) => (
                  <div key={idx} className="p-2 border border-[#E5E0D8] text-xs space-y-0.5">
                    <div className="font-semibold text-[#1F2421]">{fn.name}</div>
                    <div className="text-[11px] text-[#736F68]">{fn.venue || 'Palace Grounds'} · {fn.date || 'Scheduled'}</div>
                    {fn.notes && <div className="text-[10px] text-[#8C877D] italic">{fn.notes}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Verification Modal */}
      {showVerifyModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#E5E0D8] max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <h3 className="font-serif text-lg font-semibold text-[#1F2421]">Employee Agreement Verification</h3>
              <button onClick={() => setShowVerifyModal(false)} className="text-[#8C877D] hover:text-[#1F2421]">✕</button>
            </div>

            <form onSubmit={handleVerificationSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                  Verification Decision *
                </label>
                <select
                  value={verifyDecision}
                  onChange={(e: any) => setVerifyDecision(e.target.value)}
                  className="w-full border border-[#E5E0D8] p-2 bg-white text-xs"
                >
                  <option value="VERIFIED">VERIFIED — Completed eSign & Staged Terms Approved</option>
                  <option value="REJECTED">REJECTED — Contract Terms or Signatures Invalid</option>
                  <option value="NEEDS_CORRECTION">NEEDS_CORRECTION — Reissue Version to Client</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                  Employee Remarks & Audit Notes *
                </label>
                <textarea
                  rows={4}
                  value={verifyRemarks}
                  onChange={(e) => setVerifyRemarks(e.target.value)}
                  required
                  className="w-full border border-[#E5E0D8] p-2 text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setShowVerifyModal(false)}
                  className="px-4 py-2 border border-[#E5E0D8] text-xs font-medium text-[#736F68]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 bg-[#1F2421] text-white text-xs uppercase tracking-wider font-medium"
                >
                  Confirm Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
