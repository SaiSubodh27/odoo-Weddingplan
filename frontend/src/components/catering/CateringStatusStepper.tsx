import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  FileCheck2,
  Users2,
  UtensilsCrossed,
  Send,
  ShieldCheck
} from 'lucide-react';
import { CateringPlan, CateringPlanStatus } from '../../types/catering';
import { cateringApi } from '../../services/api';

interface CateringStatusStepperProps {
  plan: CateringPlan;
  onUpdate: () => void;
}

const LIFECYCLE_STEPS: { status: CateringPlanStatus; label: string; icon: any }[] = [
  { status: 'Draft', label: 'Draft Specs', icon: Clock },
  { status: 'Requirements Confirmed', label: 'Requirements Confirmed', icon: FileCheck2 },
  { status: 'Quotation Requested', label: 'Quotes Requested', icon: Users2 },
  { status: 'Vendor Selected', label: 'Vendor Selected', icon: ShieldCheck },
  { status: 'Menu Finalized', label: 'Menu Finalized', icon: UtensilsCrossed },
  { status: 'Sent to Vendor', label: 'Sent to Vendor', icon: Send },
  { status: 'Vendor Confirmed', label: 'Confirmed by Caterer', icon: CheckCircle2 },
];

export const CateringStatusStepper: React.FC<CateringStatusStepperProps> = ({ plan, onUpdate }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<CateringPlanStatus | null>(null);
  const [transitionNotes, setTransitionNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentIndex = LIFECYCLE_STEPS.findIndex((s) => s.status === plan.status);

  const openTransitionModal = (status: CateringPlanStatus) => {
    if (status === plan.status) return;
    setTargetStatus(status);
    setTransitionNotes('');
    setError(null);
    setIsModalOpen(true);
  };

  const handleConfirmTransition = async () => {
    if (!targetStatus) return;
    setLoading(true);
    setError(null);
    try {
      await cateringApi.updateStatus(plan.id, targetStatus, transitionNotes);
      setIsModalOpen(false);
      onUpdate();
    } catch (err: any) {
      setError(err.message || 'Status transition failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E0D8]">
        <div>
          <span className="text-[10px] uppercase tracking-wider text-[#9E7D3B] font-semibold">
            Catering Execution Stage
          </span>
          <h3 className="font-serif text-lg text-[#1F2421] flex items-center gap-2">
            <span>{plan.status}</span>
            <span className="text-xs font-sans px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#736F68] font-normal">
              Step {currentIndex + 1} of {LIFECYCLE_STEPS.length}
            </span>
          </h3>
        </div>

        {/* Quick Advance / Change dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-[#736F68] font-medium">Transition to:</label>
          <select
            value={plan.status}
            onChange={(e) => openTransitionModal(e.target.value as CateringPlanStatus)}
            className="text-xs font-semibold bg-[#FAF8F5] border border-[#E5E0D8] px-2 py-1 text-[#1F2421] focus:ring-1 focus:ring-[#9E7D3B] cursor-pointer"
          >
            {LIFECYCLE_STEPS.map((s) => (
              <option key={s.status} value={s.status}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Horizontal Lifecycle Stepper */}
      <div className="overflow-x-auto py-2">
        <div className="flex items-center min-w-[700px]">
          {LIFECYCLE_STEPS.map((step, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;
            const Icon = step.icon;

            return (
              <React.Fragment key={step.status}>
                <button
                  type="button"
                  onClick={() => openTransitionModal(step.status)}
                  className={`flex flex-col items-center group cursor-pointer focus:outline-none transition-all ${
                    isCurrent ? 'scale-105' : ''
                  }`}
                  title={`Transition to ${step.label}`}
                >
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-colors ${
                      isCurrent
                        ? 'bg-[#1F2421] border-[#9E7D3B] text-[#FAF8F5] shadow-sm'
                        : isCompleted
                        ? 'bg-[#ECFDF5] border-[#10B981] text-[#10B981]'
                        : 'bg-[#FAF8F5] border-[#E5E0D8] text-[#8C877D] group-hover:border-[#9E7D3B]'
                    }`}
                  >
                    <Icon size={16} />
                  </div>
                  <span
                    className={`text-[11px] mt-2 font-medium tracking-tight text-center max-w-[90px] leading-tight ${
                      isCurrent
                        ? 'text-[#1F2421] font-bold'
                        : isCompleted
                        ? 'text-[#10B981]'
                        : 'text-[#736F68]'
                    }`}
                  >
                    {step.label}
                  </span>
                </button>

                {idx < LIFECYCLE_STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 transition-colors ${
                      idx < currentIndex ? 'bg-[#10B981]' : 'bg-[#E5E0D8]'
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Transition Confirmation Modal */}
      {isModalOpen && targetStatus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-md p-6 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
              <AlertCircle size={18} className="text-[#9E7D3B]" />
              <h3 className="font-serif text-lg text-[#1F2421]">Confirm Stage Transition</h3>
            </div>

            <div className="text-xs text-[#736F68] space-y-2">
              <p>
                You are transitioning this catering plan from <b>"{plan.status}"</b> to{' '}
                <b className="text-[#1F2421]">"{targetStatus}"</b>.
              </p>
              {targetStatus === 'Vendor Selected' && !plan.selectedVendorId && (
                <div className="p-2 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-[11px]">
                  Warning: Advancing to 'Vendor Selected' requires an accepted winning quotation.
                </div>
              )}
              {targetStatus === 'Menu Finalized' && plan.menuItems.length === 0 && (
                <div className="p-2 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-[11px]">
                  Warning: Advancing to 'Menu Finalized' requires at least 1 menu item or preset.
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Audit Trail Notes (Optional)
              </label>
              <textarea
                value={transitionNotes}
                onChange={(e) => setTransitionNotes(e.target.value)}
                placeholder="Reason for change, client sign-off, or vendor confirmation reference..."
                rows={3}
                className="w-full text-xs p-2.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:ring-1 focus:ring-[#9E7D3B]"
              />
            </div>

            {error && (
              <div className="p-2.5 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs">
                {error}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                disabled={loading}
                className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68] hover:bg-[#FAF8F5]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmTransition}
                disabled={loading}
                className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B] transition-colors flex items-center gap-1.5"
              >
                {loading ? 'Validating...' : 'Update Stage'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
