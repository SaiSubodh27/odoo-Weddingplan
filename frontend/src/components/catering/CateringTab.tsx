import React, { useState, useEffect, useCallback } from 'react';
import { 
  UtensilsCrossed, 
  Calendar, 
  Plus, 
  Edit3, 
  FileDown, 
  History, 
  Sparkles,
} from 'lucide-react';
import { WeddingProject } from '../../types/project';
import { CateringPlan, CateringCommunicationLog } from '../../types/catering';
import { cateringApi } from '../../services/api';
import { CateringStatusStepper } from './CateringStatusStepper';
import { CateringRequirementsModal } from './CateringRequirementsModal';
import { CateringMenuSection } from './CateringMenuSection';
import { CateringQuotationsSection } from './CateringQuotationsSection';

interface CateringTabProps {
  project: WeddingProject;
  onRefresh: () => void;
}

export const CateringTab: React.FC<CateringTabProps> = ({ project, onRefresh }) => {
  const [plans, setPlans] = useState<CateringPlan[]>([]);
  const [selectedFunctionId, setSelectedFunctionId] = useState<string>(
    project.functions.length > 0 ? project.functions[0].id : ''
  );
  const [loading, setLoading] = useState(true);
  // error state
  const [, setError] = useState<string | null>(null);
  const [isEditReqOpen, setIsEditReqOpen] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [communications, setCommunications] = useState<CateringCommunicationLog[]>([]);

  const fetchPlans = useCallback(async () => {
    try {
      setLoading(true);
      const data = await cateringApi.getProjectCateringPlans(project.id);
      setPlans(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load catering plans.');
    } finally {
      setLoading(false);
    }
  }, [project.id]);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  // Find active plan for selected function
  const activePlan = plans.find((p) => p.weddingFunctionId === selectedFunctionId);

  // Fetch communications when active plan changes
  useEffect(() => {
    if (activePlan) {
      cateringApi.listCommunications(activePlan.id)
        .then(setCommunications)
        .catch(() => setCommunications([]));
    } else {
      setCommunications([]);
    }
  }, [activePlan?.id]);

  const selectedFunction = project.functions.find((f) => f.id === selectedFunctionId);

  const handleInitializePlan = async () => {
    if (!selectedFunctionId) return;
    setInitLoading(true);
    try {
      await cateringApi.createPlan(project.id, selectedFunctionId, {
        guestCount: project.guestCount || 200,
        serviceStyle: 'Silver Platter',
      });
      await fetchPlans();
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to initialize catering plan.');
    } finally {
      setInitLoading(false);
    }
  };

  const formatINR = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '₹ 0';
    return `₹ ${Number(val).toLocaleString('en-IN')}`;
  };

  if (loading && plans.length === 0) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center text-xs text-[#736F68]">
        Loading catering dossiers and banquet configurations...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Function Selector Pills */}
      {project.functions.length === 0 ? (
        <div className="p-8 bg-[#FFFFFF] border border-[#E5E0D8] text-center space-y-2">
          <Calendar size={32} className="mx-auto text-[#9E7D3B]" />
          <h3 className="font-serif text-lg text-[#1F2421]">No Wedding Functions Registered</h3>
          <p className="text-xs text-[#736F68]">
            Please add wedding functions (e.g. Sangeet, Mehendi, Reception) under the Functions tab first.
          </p>
        </div>
      ) : (
        <>
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-[#9E7D3B]" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[#1F2421]">
                Select Ceremony Event:
              </span>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {project.functions.map((func) => {
                const isSelected = func.id === selectedFunctionId;
                const hasPlan = plans.some((p) => p.weddingFunctionId === func.id);

                return (
                  <button
                    key={func.id}
                    onClick={() => setSelectedFunctionId(func.id)}
                    className={`px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5 border ${
                      isSelected
                        ? 'bg-[#1F2421] text-[#FAF8F5] border-[#1F2421]'
                        : 'bg-[#FAF8F5] text-[#736F68] border-[#E5E0D8] hover:border-[#9E7D3B]'
                    }`}
                  >
                    <span>{func.functionName}</span>
                    {hasPlan && (
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isSelected ? 'bg-[#9E7D3B]' : 'bg-[#10B981]'
                        }`}
                        title="Catering Plan Configured"
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Plan Content */}
          {!activePlan ? (
            /* Uninitialized function */
            <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center space-y-4">
              <UtensilsCrossed size={36} className="mx-auto text-[#9E7D3B]" />
              <div className="space-y-1">
                <h3 className="font-serif text-xl text-[#1F2421]">
                  No Catering Dossier Initialized for "{selectedFunction?.functionName}"
                </h3>
                <p className="text-xs text-[#736F68] max-w-md mx-auto">
                  Initialize a catering plan to manage dietary guest counts, build custom menus or apply luxury presets, and compare vendor quotations.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  disabled={initLoading}
                  onClick={handleInitializePlan}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold transition-colors"
                >
                  <Plus size={15} />
                  <span>{initLoading ? 'Initializing...' : 'Initialize Catering Plan'}</span>
                </button>
              </div>
            </div>
          ) : (
            /* Active Catering Plan View */
            <div className="space-y-6">
              {/* 1. Lifecycle Stepper */}
              <CateringStatusStepper plan={activePlan} onUpdate={fetchPlans} />

              {/* 2. Requirements & Overview Card */}
              <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E0D8]">
                  <div className="flex items-center gap-2">
                    <Sparkles size={18} className="text-[#9E7D3B]" />
                    <h3 className="font-serif text-xl text-[#1F2421]">
                      Catering Specifications & Dietary Distribution
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <a
                      href={cateringApi.getCateringPlanPdfUrl(activePlan.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#FAF8F5] hover:bg-[#EFEBE4] border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#1F2421] transition-colors"
                    >
                      <FileDown size={13} className="text-[#9E7D3B]" />
                      <span>Download PDF</span>
                    </a>

                    <button
                      type="button"
                      onClick={() => setIsEditReqOpen(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold transition-colors"
                    >
                      <Edit3 size={13} />
                      <span>Edit Requirements</span>
                    </button>
                  </div>
                </div>

                {/* Specs Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold block">
                      Target Guests (Pax)
                    </span>
                    <span className="font-serif text-lg font-bold text-[#1F2421]">
                      {activePlan.guestCount} Pax
                    </span>
                    <span className="text-[10px] text-[#736F68] block">
                      (Default: {project.guestCount} Pax)
                    </span>
                  </div>

                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold block">
                      Dietary Distribution
                    </span>
                    <div className="text-[11px] space-y-0.5 text-[#1F2421]">
                      <div>Veg: <b>{activePlan.vegCount}</b></div>
                      <div>Non-Veg: <b>{activePlan.nonVegCount}</b></div>
                      <div>Jain: <b>{activePlan.jainCount}</b></div>
                    </div>
                  </div>

                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold block">
                      Service Style & Timings
                    </span>
                    <span className="font-bold text-[#1F2421] block">
                      {activePlan.serviceStyle}
                    </span>
                    <span className="text-[#736F68] block">
                      {activePlan.serviceTimings || 'Service timings TBD'}
                    </span>
                  </div>

                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold block">
                      Budget & Agreed Cost
                    </span>
                    <span className="text-xs text-[#736F68] block">
                      Budget: <b>{formatINR(activePlan.budget)}</b>
                    </span>
                    <span className="text-sm font-bold text-[#9E7D3B] block">
                      Agreed: {formatINR(activePlan.agreedCost)}
                    </span>
                  </div>
                </div>

                {activePlan.dietaryNotes && (
                  <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#736F68]">
                    <b className="text-[#1F2421]">Dietary & Allergy Notes:</b> {activePlan.dietaryNotes}
                  </div>
                )}
              </div>

              {/* 3. Curated Menu Section */}
              <CateringMenuSection plan={activePlan} onUpdate={fetchPlans} />

              {/* 4. Multi-Vendor Quotations & Costing Section */}
              <CateringQuotationsSection plan={activePlan} onUpdate={fetchPlans} />

              {/* 5. Communication Audit Log */}
              {communications.length > 0 && (
                <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
                    <History size={16} className="text-[#9E7D3B]" />
                    <h3 className="font-serif text-lg text-[#1F2421]">
                      Communications & Quotation Sharing Audit Log
                    </h3>
                  </div>

                  <div className="divide-y divide-[#E5E0D8] text-xs">
                    {communications.map((comm) => (
                      <div key={comm.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#1F2421]">{comm.communicationType}</span>
                            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#736F68]">
                              Status: {comm.status}
                            </span>
                          </div>
                          <p className="text-[#736F68]">
                            Recipient: {comm.recipientPhone || 'Vendor'} • Logged by: {comm.initiatedBy}
                          </p>
                        </div>
                        <span className="text-[11px] text-[#736F68]">
                          {new Date(comm.createdAt).toLocaleString('en-IN', {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Edit Requirements Modal */}
              {isEditReqOpen && (
                <CateringRequirementsModal
                  plan={activePlan}
                  onClose={() => setIsEditReqOpen(false)}
                  onSuccess={fetchPlans}
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};
