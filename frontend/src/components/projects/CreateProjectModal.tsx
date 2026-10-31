import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { projectApi } from '../../services/api';
import { EligibleBooking, WeddingProject } from '../../types/project';
import { useClients } from '../../context/ClientContext';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: (project: WeddingProject) => void;
}

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onProjectCreated
}) => {
  const { clients } = useClients();
  const [eligibleBookings, setEligibleBookings] = useState<EligibleBooking[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [selectedClientId, setSelectedClientId] = useState<string>('');
  const [projectName, setProjectName] = useState<string>('');
  const [weddingDate, setWeddingDate] = useState<string>('');
  const [location, setLocation] = useState<string>('');
  const [guestCount, setGuestCount] = useState<number>(100);
  const [estimatedBudget, setEstimatedBudget] = useState<string>('0');
  const [packageTier, setPackageTier] = useState<string>('Full-Service');
  const [projectManagerName, setProjectManagerName] = useState<string>('Maharani Gayatri Singh');
  const [notes, setNotes] = useState<string>('');

  // Fetch eligible confirmed bookings on modal open
  useEffect(() => {
    if (!isOpen) return;

    setErrorMessage(null);
    setLoading(true);

    projectApi.getEligibleBookings()
      .then((data: EligibleBooking[]) => {
        if (Array.isArray(data) && data.length > 0) {
          setEligibleBookings(data);
          selectBooking(data[0]);
        } else {
          // Fallback to local context confirmed clients if backend has no active projects yet
          const confirmedClients = clients.filter(c => c.status === 'Confirmed');
          const mapped: EligibleBooking[] = confirmedClients.map(c => ({
            clientId: c.id,
            partner1Name: c.partner1Name,
            partner2Name: c.partner2Name,
            coupleName: `${c.partner1Name} & ${c.partner2Name}`,
            weddingDate: c.weddingDate,
            weddingLocation: c.weddingLocation,
            expectedGuestCount: c.expectedGuestCount,
            estimatedBudget: c.estimatedBudget,
            servicePackage: c.servicePackage,
            status: c.status,
            createdAt: c.createdAt
          }));
          setEligibleBookings(mapped);
          if (mapped.length > 0) {
            selectBooking(mapped[0]);
          }
        }
      })
      .catch(() => {
        // Fallback to local clients
        const confirmedClients = clients.filter(c => c.status === 'Confirmed');
        const mapped: EligibleBooking[] = confirmedClients.map(c => ({
          clientId: c.id,
          partner1Name: c.partner1Name,
          partner2Name: c.partner2Name,
          coupleName: `${c.partner1Name} & ${c.partner2Name}`,
          weddingDate: c.weddingDate,
          weddingLocation: c.weddingLocation,
          expectedGuestCount: c.expectedGuestCount,
          estimatedBudget: c.estimatedBudget,
          servicePackage: c.servicePackage,
          status: c.status,
          createdAt: c.createdAt
        }));
        setEligibleBookings(mapped);
        if (mapped.length > 0) {
          selectBooking(mapped[0]);
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, clients]);

  const selectBooking = (booking: EligibleBooking) => {
    setSelectedClientId(booking.clientId);
    setProjectName(`${booking.coupleName} Royal Wedding`);
    setWeddingDate(booking.weddingDate);
    setLocation(booking.weddingLocation);
    setGuestCount(booking.expectedGuestCount);
    setEstimatedBudget(String(booking.estimatedBudget));
    setPackageTier(booking.servicePackage || 'Full-Service');
  };

  const handleBookingChange = (clientId: string) => {
    setSelectedClientId(clientId);
    const booking = eligibleBookings.find(b => b.clientId === clientId);
    if (booking) {
      selectBooking(booking);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientId) {
      setErrorMessage('Please select a confirmed client booking dossier.');
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        clientId: selectedClientId,
        projectName: projectName.trim(),
        weddingDate,
        location: location.trim(),
        guestCount: Number(guestCount),
        estimatedBudget,
        packageTier,
        projectManagerName: projectManagerName.trim(),
        notes: notes.trim() || undefined
      };

      const created = await projectApi.create(payload);
      onProjectCreated(created);
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create wedding project. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="p-6 bg-[#FAF8F5] border-b border-[#E5E0D8] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#FFFFFF] border border-[#E5E0D8] text-[#9E7D3B]">
              <Sparkles size={18} />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-[#9E7D3B] font-semibold">
                Phase 3 · Project Setup
              </div>
              <h2 className="font-serif text-2xl text-[#1F2421]">
                Initialize Wedding Project
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] text-[#736F68] hover:text-[#1F2421] transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {errorMessage && (
            <div className="p-3 bg-[#FDF2F2] border border-[#E0B4B4] text-xs text-[#9B2C2C] flex items-start gap-2">
              <AlertCircle size={15} className="shrink-0 mt-0.5 text-[#9B2C2C]" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Booking Selector */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
              Select Confirmed Wedding Booking Dossier *
            </label>
            {loading ? (
              <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#736F68]">
                Scanning confirmed bookings directory...
              </div>
            ) : eligibleBookings.length === 0 ? (
              <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#736F68] space-y-2">
                <p className="font-medium text-[#1F2421]">No unassigned confirmed bookings available.</p>
                <p>
                  To set up a wedding project, a client dossier must be in <strong className="text-[#9E7D3B]">Confirmed</strong> status. You can update a client's status to 'Confirmed' in the Client Directory.
                </p>
              </div>
            ) : (
              <select
                value={selectedClientId}
                onChange={(e) => handleBookingChange(e.target.value)}
                className="w-full px-3 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] font-medium focus:outline-none focus:border-[#1F2421]"
                required
              >
                {eligibleBookings.map((b) => (
                  <option key={b.clientId} value={b.clientId}>
                    {b.clientId} — {b.coupleName} ({b.weddingLocation} · {new Date(b.weddingDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })})
                  </option>
                ))}
              </select>
            )}
            <p className="text-[11px] text-[#736F68] mt-1.5">
              Only client dossiers with confirmed agreements are eligible for project creation.
            </p>
          </div>

          {/* Pre-populated Details Form */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-[#E5E0D8]">
            <div className="sm:col-span-2">
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Project Name *
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] font-medium focus:outline-none focus:border-[#1F2421]"
                placeholder="e.g. Ananya & Veer Palace Wedding"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Target Wedding Date *
              </label>
              <div className="relative">
                <input
                  type="date"
                  value={weddingDate}
                  onChange={(e) => setWeddingDate(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Destination Palace Venue *
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                placeholder="e.g. The Leela Palace, Udaipur"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Expected Guests
              </label>
              <input
                type="number"
                min={1}
                value={guestCount}
                onChange={(e) => setGuestCount(Number(e.target.value))}
                required
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Estimated Budget (₹)
              </label>
              <input
                type="text"
                value={estimatedBudget}
                onChange={(e) => setEstimatedBudget(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                placeholder="e.g. ₹ 1.85 Cr or 18500000"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Service Package Tier
              </label>
              <select
                value={packageTier}
                onChange={(e) => setPackageTier(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              >
                <option value="Full-Service">Full-Service Royal Production</option>
                <option value="Partial-Service">Partial-Service Heritage Coordination</option>
                <option value="Day-of Coordination">Day-of Venue & Concierge Coordination</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Principal Project Manager *
              </label>
              <input
                type="text"
                value={projectManagerName}
                onChange={(e) => setProjectManagerName(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                Initial Operational Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                placeholder="Key setup notes, VIP protocol, venue coordination instructions..."
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-[#E5E0D8] flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-medium text-[#736F68] hover:bg-[#FAF8F5] transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting || eligibleBookings.length === 0}
              className="px-6 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <CheckCircle size={14} className="text-[#9E7D3B]" />
              <span>{submitting ? 'Generating Project...' : 'Create Wedding Project'}</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
