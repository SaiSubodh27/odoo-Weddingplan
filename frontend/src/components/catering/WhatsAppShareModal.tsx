import React, { useState } from 'react';
import { 
  X, 
  Send, 
  Check, 
  Copy, 
  ExternalLink, 
  MessageSquare, 
  AlertCircle,
  ShieldCheck
} from 'lucide-react';
import { CateringWhatsAppShareResponse } from '../../types/catering';
import { cateringApi } from '../../services/api';

interface WhatsAppShareModalProps {
  cateringId: string;
  quotationId?: string;
  vendorId?: string;
  defaultVendorName?: string;
  defaultPhone?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const WhatsAppShareModal: React.FC<WhatsAppShareModalProps> = ({
  cateringId,
  quotationId,
  vendorId,
  defaultVendorName,
  defaultPhone,
  onClose,
  onSuccess,
}) => {
  const [phone, setPhone] = useState(defaultPhone || '');
  const [customMessage, setCustomMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shareResult, setShareResult] = useState<CateringWhatsAppShareResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerateShare = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await cateringApi.shareWhatsApp(cateringId, {
        quotationId,
        vendorId,
        recipientPhone: phone,
        customMessage: customMessage || undefined,
      });
      setShareResult(res);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to generate WhatsApp share link.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (!shareResult) return;
    navigator.clipboard.writeText(shareResult.shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-xl p-6 space-y-5 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
          <div className="flex items-center gap-2">
            <MessageSquare size={18} className="text-[#10B981]" />
            <h3 className="font-serif text-lg text-[#1F2421]">
              Share Catering Dossier via WhatsApp
            </h3>
          </div>
          <button onClick={onClose} className="text-[#8C877D] hover:text-[#1F2421]">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs flex items-center gap-2">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        {!shareResult ? (
          <form onSubmit={handleGenerateShare} className="space-y-4">
            <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1 text-xs">
              <span className="font-semibold text-[#1F2421]">Target Vendor Partner:</span>{' '}
              <span className="text-[#736F68]">{defaultVendorName || 'Registered Caterer'}</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Recipient WhatsApp Phone Number *
              </label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
              />
              <span className="text-[11px] text-[#736F68] mt-0.5 block">
                Standard 10-digit Indian mobile or international format with country code.
              </span>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Custom Concierge Note (Optional)
              </label>
              <textarea
                rows={3}
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                placeholder="e.g. Please review the updated guest pax, Jain counter requirements, and service schedule..."
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
              />
            </div>

            <div className="p-3 bg-[#F0FDF4] border border-[#BBF7D0] text-[11px] text-[#166534] space-y-1">
              <div className="font-semibold flex items-center gap-1.5">
                <ShieldCheck size={14} />
                <span>Verified Direct WhatsApp Link Protocol</span>
              </div>
              <p>
                Generates an authentic, pre-filled <code>wa.me</code> deep-link encoded with celebration details, guest pax, and quotation reference. Accurately logs action as "Initiated" in audit trail.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 bg-[#10B981] hover:bg-[#059669] text-white text-xs uppercase tracking-wider font-semibold transition-colors flex items-center gap-1.5"
              >
                <Send size={13} />
                <span>{loading ? 'Composing...' : 'Generate WhatsApp Link'}</span>
              </button>
            </div>
          </form>
        ) : (
          /* Result & Action Buttons */
          <div className="space-y-4">
            <div className="p-3 bg-[#ECFDF5] border border-[#A7F3D0] text-xs font-semibold text-[#065F46] flex items-center gap-2">
              <Check size={16} />
              <span>WhatsApp Deep-Link Generated & Logged (ID: {shareResult.communicationId})</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider block mb-1">
                Pre-Filled Message Preview
              </label>
              <pre className="text-xs p-3 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] whitespace-pre-wrap font-sans max-h-48 overflow-y-auto leading-relaxed">
                {shareResult.messageText}
              </pre>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-2 pt-2">
              <a
                href={shareResult.shareUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 bg-[#10B981] hover:bg-[#059669] text-white text-xs uppercase tracking-wider font-semibold transition-colors"
              >
                <ExternalLink size={14} />
                <span>Open in WhatsApp Web / App</span>
              </a>

              <button
                type="button"
                onClick={handleCopyLink}
                className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-4 py-2.5 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] text-xs uppercase tracking-wider font-semibold text-[#1F2421] transition-colors"
              >
                {copied ? <Check size={14} className="text-[#10B981]" /> : <Copy size={14} />}
                <span>{copied ? 'Link Copied!' : 'Copy wa.me Link'}</span>
              </button>
            </div>

            <div className="pt-3 border-t border-[#E5E0D8] flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
