import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  Plus, 
  FileDown, 
  Share2, 
  CheckCircle, 
  Trophy, 
  Phone,
  X,
  FileText
} from 'lucide-react';
import { CateringPlan, CateringQuotation, Vendor } from '../../types/catering';
import { cateringApi, vendorApi } from '../../services/api';
import { WhatsAppShareModal } from './WhatsAppShareModal';

interface CateringQuotationsSectionProps {
  plan: CateringPlan;
  onUpdate: () => void;
}

export const CateringQuotationsSection: React.FC<CateringQuotationsSectionProps> = ({
  plan,
  onUpdate,
}) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendorId, setSelectedVendorId] = useState('');
  const [perPersonRate, setPerPersonRate] = useState<number | ''>(2500);
  const [totalGuestCount, setTotalGuestCount] = useState<number | ''>(plan.guestCount);
  const [equipmentCharges, setEquipmentCharges] = useState<number | ''>(25000);
  const [gstRatePercent, setGstRatePercent] = useState<number>(18);
  const [customGst, setCustomGst] = useState<number | ''>('');
  const [quotationNotes, setQuotationNotes] = useState('');
  const [validityDate, setValidityDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WhatsApp modal state
  const [activeWhatsAppQuote, setActiveWhatsAppQuote] = useState<CateringQuotation | null>(null);

  useEffect(() => {
    vendorApi.list().then((list) => {
      setVendors(list);
      if (list.length > 0 && !selectedVendorId) {
        setSelectedVendorId(list[0].id);
      }
    }).catch(() => {});
  }, []);

  const openAddQuoteModal = () => {
    setSelectedVendorId(vendors.length > 0 ? vendors[0].id : '');
    setPerPersonRate(2500);
    setTotalGuestCount(plan.guestCount);
    setEquipmentCharges(25000);
    setGstRatePercent(18);
    setCustomGst('');
    setQuotationNotes('');
    setValidityDate('');
    setError(null);
    setIsAddModalOpen(true);
  };

  // Real-time Costing Preview
  const rateNum = Number(perPersonRate) || 0;
  const guestsNum = Number(totalGuestCount) || 0;
  const equipNum = Number(equipmentCharges) || 0;
  const effectiveGstRate = gstRatePercent === -1 ? (Number(customGst) || 0) : gstRatePercent;

  const foodSubtotal = Math.round(rateNum * guestsNum * 100) / 100;
  const taxableSubtotal = foodSubtotal + equipNum;
  const gstAmount = Math.round(taxableSubtotal * (effectiveGstRate / 100) * 100) / 100;
  const totalAmount = Math.round((taxableSubtotal + gstAmount) * 100) / 100;

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVendorId) {
      setError('Please select a registered catering vendor.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await cateringApi.createQuotation(plan.id, {
        vendorId: selectedVendorId,
        perPersonRate: rateNum,
        totalGuestCount: guestsNum,
        equipmentCharges: equipNum,
        gstRatePercent: effectiveGstRate,
        validityDate: validityDate || null,
        notes: quotationNotes || null,
      });
      setIsAddModalOpen(false);
      onUpdate();
    } catch (err: any) {
      setError(err.message || 'Failed to record vendor quotation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWinning = async (quote: CateringQuotation) => {
    if (
      !window.confirm(
        `Select ${quote.vendorName || 'this vendor'} as the winning caterer? This will lock in ₹${quote.totalAmount.toLocaleString()} as the agreed cost.`
      )
    ) {
      return;
    }

    try {
      await cateringApi.selectWinningQuotation(plan.id, quote.id);
      onUpdate();
    } catch (err: any) {
      alert(err.message || 'Failed to select winning quotation.');
    }
  };

  const formatINR = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '₹ 0';
    return `₹ ${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
      {/* Header & Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E0D8]">
        <div>
          <div className="flex items-center gap-2">
            <DollarSign size={18} className="text-[#9E7D3B]" />
            <h3 className="font-serif text-xl text-[#1F2421]">Vendor Quotations & Costing</h3>
          </div>
          <p className="text-xs text-[#736F68] mt-1">
            Compare multi-vendor bids with transparent decimal-safe GST calculations
          </p>
        </div>

        <button
          type="button"
          onClick={openAddQuoteModal}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold transition-colors"
        >
          <Plus size={14} />
          <span>Record Vendor Quotation</span>
        </button>
      </div>

      {/* Selected Vendor Banner if Locked */}
      {plan.selectedVendorId && (
        <div className="p-4 bg-[#FAF8F5] border-l-4 border-[#9E7D3B] border border-[#E5E0D8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <Trophy size={16} className="text-[#9E7D3B]" />
              <span className="font-serif text-sm font-bold text-[#1F2421]">
                Official Winning Caterer Selected
              </span>
            </div>
            <p className="text-xs text-[#736F68]">
              Assigned Partner:{' '}
              <b className="text-[#1F2421]">
                {plan.selectedVendor?.name || plan.selectedVendorId}
              </b>{' '}
              • Agreed Cost:{' '}
              <b className="text-[#1F2421]">{formatINR(plan.agreedCost)}</b>
            </p>
          </div>

          <a
            href={cateringApi.getCateringPlanPdfUrl(plan.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#FFFFFF] hover:bg-[#FAF8F5] border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#1F2421] transition-colors"
          >
            <FileDown size={13} className="text-[#9E7D3B]" />
            <span>Event Spec PDF</span>
          </a>
        </div>
      )}

      {/* Empty State */}
      {plan.quotations.length === 0 ? (
        <div className="text-center py-10 px-4 border border-dashed border-[#E5E0D8] bg-[#FAF8F5] space-y-2">
          <FileText size={32} className="mx-auto text-[#8C877D]" />
          <h4 className="font-serif text-base text-[#1F2421]">No Quotations Submitted Yet</h4>
          <p className="text-xs text-[#736F68] max-w-sm mx-auto">
            Record incoming vendor bids to compare food subtotals, equipment charges, and GST breakdown.
          </p>
          <div className="pt-2">
            <button
              onClick={openAddQuoteModal}
              className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
            >
              Add First Quotation
            </button>
          </div>
        </div>
      ) : (
        /* Quotation Cards Grid */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {plan.quotations.map((quote) => {
            const isAccepted = quote.status === 'Accepted';
            const isRejected = quote.status === 'Rejected';

            return (
              <div
                key={quote.id}
                className={`border transition-all p-5 space-y-4 ${
                  isAccepted
                    ? 'border-[#9E7D3B] bg-[#FFFDF9] shadow-sm'
                    : isRejected
                    ? 'border-[#E5E0D8] bg-[#FAF8F5] opacity-75'
                    : 'border-[#E5E0D8] bg-[#FFFFFF] hover:border-[#9E7D3B]'
                }`}
              >
                {/* Header: Vendor Name & Status */}
                <div className="flex items-start justify-between gap-2 pb-3 border-b border-[#E5E0D8]">
                  <div className="space-y-0.5">
                    <h4 className="font-serif text-base font-bold text-[#1F2421]">
                      {quote.vendorName || quote.vendorId}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-[#736F68]">
                      {quote.vendorCity && <span>{quote.vendorCity}</span>}
                      {quote.vendorPhone && (
                        <span>• <Phone size={11} className="inline mr-0.5" />{quote.vendorPhone}</span>
                      )}
                    </div>
                  </div>

                  <span
                    className={`text-[10px] uppercase tracking-wider px-2 py-0.5 border font-semibold ${
                      isAccepted
                        ? 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]'
                        : isRejected
                        ? 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]'
                        : 'bg-[#FAF8F5] text-[#1F2421] border-[#E5E0D8]'
                    }`}
                  >
                    {quote.status}
                  </span>
                </div>

                {/* Financial Costing Breakdown */}
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between text-[#736F68]">
                    <span>Rate per Guest ({quote.totalGuestCount} Pax):</span>
                    <span className="font-medium text-[#1F2421]">{formatINR(quote.perPersonRate)}</span>
                  </div>
                  <div className="flex justify-between text-[#736F68]">
                    <span>Food Subtotal:</span>
                    <span className="font-medium text-[#1F2421]">{formatINR(quote.foodSubtotal)}</span>
                  </div>
                  <div className="flex justify-between text-[#736F68]">
                    <span>Kitchen & Silverware Rentals:</span>
                    <span className="font-medium text-[#1F2421]">{formatINR(quote.equipmentCharges)}</span>
                  </div>
                  <div className="flex justify-between text-[#736F68]">
                    <span>Configured GST ({quote.gstRatePercent}%):</span>
                    <span className="font-medium text-[#1F2421]">{formatINR(quote.gstAmount)}</span>
                  </div>
                  <div className="pt-2 border-t border-[#E5E0D8] flex justify-between text-sm font-bold text-[#1F2421]">
                    <span>Total Investment:</span>
                    <span className="text-[#9E7D3B]">{formatINR(quote.totalAmount)}</span>
                  </div>
                </div>

                {quote.notes && (
                  <p className="text-[11px] text-[#736F68] bg-[#FAF8F5] p-2 border border-[#E5E0D8] italic">
                    "{quote.notes}"
                  </p>
                )}

                {/* Action Bar */}
                <div className="pt-3 border-t border-[#E5E0D8] flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    {/* PDF Download */}
                    <a
                      href={cateringApi.getQuotationPdfUrl(plan.id, quote.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-[#736F68] hover:text-[#1F2421] hover:bg-[#FAF8F5] border border-[#E5E0D8] rounded transition-colors flex items-center gap-1 text-[11px] font-medium"
                      title="Download Branded PDF"
                    >
                      <FileDown size={13} className="text-[#9E7D3B]" />
                      <span>PDF</span>
                    </a>

                    {/* WhatsApp Share */}
                    <button
                      type="button"
                      onClick={() => setActiveWhatsAppQuote(quote)}
                      className="p-1.5 text-[#10B981] hover:text-[#059669] hover:bg-[#ECFDF5] border border-[#A7F3D0] rounded transition-colors flex items-center gap-1 text-[11px] font-medium"
                      title="Share via WhatsApp"
                    >
                      <Share2 size={13} />
                      <span>WhatsApp</span>
                    </button>
                  </div>

                  {/* Select as Winning Button */}
                  {!isAccepted && quote.status !== 'Rejected' && (
                    <button
                      type="button"
                      onClick={() => handleSelectWinning(quote)}
                      className="px-3 py-1.5 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-[11px] uppercase tracking-wider font-semibold transition-colors flex items-center gap-1"
                    >
                      <CheckCircle size={12} />
                      <span>Select Winning Caterer</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Quotation Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-xl my-8 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <DollarSign size={18} className="text-[#9E7D3B]" />
                <h3 className="font-serif text-lg text-[#1F2421]">Record Vendor Quotation</h3>
              </div>
              <button onClick={() => setIsAddModalOpen(false)} className="text-[#8C877D]">
                <X size={18} />
              </button>
            </div>

            {error && (
              <div className="p-2.5 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateQuotation} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Select Catering Vendor Partner *
                </label>
                <select
                  required
                  value={selectedVendorId}
                  onChange={(e) => setSelectedVendorId(e.target.value)}
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1 font-semibold"
                >
                  <option value="">-- Choose Vendor --</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.city}) - {v.phone}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Rate per Guest (₹ INR) *
                  </label>
                  <input
                    type="number"
                    min={1}
                    step={10}
                    required
                    value={perPersonRate}
                    onChange={(e) => setPerPersonRate(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Guest Count (Pax) *
                  </label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={totalGuestCount}
                    onChange={(e) => setTotalGuestCount(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Kitchen & Silverware Rentals (₹ INR)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={500}
                    value={equipmentCharges}
                    onChange={(e) => setEquipmentCharges(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Applicable GST Rate *
                  </label>
                  <select
                    value={gstRatePercent}
                    onChange={(e) => setGstRatePercent(Number(e.target.value))}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1 font-semibold"
                  >
                    <option value={18}>18.00% (Standard Luxury Catering Composite)</option>
                    <option value={12}>12.00% (Restaurant Services)</option>
                    <option value={5}>5.00% (Concessional / Non-AC Banqueting)</option>
                    <option value={0}>0.00% (Exempt)</option>
                    <option value={-1}>Custom Rate (%)</option>
                  </select>
                  {gstRatePercent === -1 && (
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.1}
                      placeholder="Enter custom GST %"
                      value={customGst}
                      onChange={(e) => setCustomGst(e.target.value === '' ? '' : Number(e.target.value))}
                      className="w-full text-xs p-2 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] mt-1.5"
                    />
                  )}
                </div>
              </div>

              {/* Real-time Calculation Summary Card */}
              <div className="p-3.5 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1.5 text-xs">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-[#9E7D3B] block">
                  Live Costing Engine Breakdown
                </span>
                <div className="flex justify-between text-[#736F68]">
                  <span>Food Subtotal ({guestsNum} Pax @ {formatINR(rateNum)}):</span>
                  <span className="font-semibold text-[#1F2421]">{formatINR(foodSubtotal)}</span>
                </div>
                <div className="flex justify-between text-[#736F68]">
                  <span>Taxable Subtotal (Food + Rentals):</span>
                  <span className="font-semibold text-[#1F2421]">{formatINR(taxableSubtotal)}</span>
                </div>
                <div className="flex justify-between text-[#736F68]">
                  <span>GST Amount ({effectiveGstRate}%):</span>
                  <span className="font-semibold text-[#1F2421]">{formatINR(gstAmount)}</span>
                </div>
                <div className="pt-2 border-t border-[#E5E0D8] flex justify-between font-bold text-sm text-[#1F2421]">
                  <span>Total Quoted Investment:</span>
                  <span className="text-[#9E7D3B]">{formatINR(totalAmount)}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Validity Deadline
                  </label>
                  <input
                    type="date"
                    value={validityDate}
                    onChange={(e) => setValidityDate(e.target.value)}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Notes & Inclusions
                  </label>
                  <input
                    type="text"
                    value={quotationNotes}
                    onChange={(e) => setQuotationNotes(e.target.value)}
                    placeholder="e.g. Includes live tandoor and royal silver chafing vessels..."
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
                >
                  {loading ? 'Recording...' : 'Record Quotation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* WhatsApp Modal */}
      {activeWhatsAppQuote && (
        <WhatsAppShareModal
          cateringId={plan.id}
          quotationId={activeWhatsAppQuote.id}
          vendorId={activeWhatsAppQuote.vendorId}
          defaultVendorName={activeWhatsAppQuote.vendorName || undefined}
          defaultPhone={activeWhatsAppQuote.vendorPhone || undefined}
          onClose={() => setActiveWhatsAppQuote(null)}
          onSuccess={onUpdate}
        />
      )}
    </div>
  );
};
