import React, { useState } from 'react';
import { X, Sparkles, AlertCircle } from 'lucide-react';
import { CateringPlan } from '../../types/catering';
import { cateringApi } from '../../services/api';

interface CateringRequirementsModalProps {
  plan: CateringPlan;
  onClose: () => void;
  onSuccess: () => void;
}

export const CateringRequirementsModal: React.FC<CateringRequirementsModalProps> = ({
  plan,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    guestCount: plan.guestCount,
    vegCount: plan.vegCount,
    nonVegCount: plan.nonVegCount,
    jainCount: plan.jainCount,
    dietaryNotes: plan.dietaryNotes || '',
    serviceStyle: plan.serviceStyle || 'Silver Platter',
    serviceTimings: plan.serviceTimings || '',
    location: plan.location || '',
    cuisinePreferences: plan.cuisinePreferences || '',
    budget: plan.budget || '',
    notes: plan.notes || '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await cateringApi.updatePlan(plan.id, {
        guestCount: Number(formData.guestCount),
        vegCount: Number(formData.vegCount),
        nonVegCount: Number(formData.nonVegCount),
        jainCount: Number(formData.jainCount),
        dietaryNotes: formData.dietaryNotes || null,
        serviceStyle: formData.serviceStyle,
        serviceTimings: formData.serviceTimings || null,
        location: formData.location || null,
        cuisinePreferences: formData.cuisinePreferences || null,
        budget: formData.budget ? Number(formData.budget) : null,
        notes: formData.notes || null,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update catering requirements.');
    } finally {
      setLoading(false);
    }
  };

  const totalDietary = Number(formData.vegCount) + Number(formData.nonVegCount) + Number(formData.jainCount);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-2xl my-8 p-6 space-y-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-[#9E7D3B]" />
            <h3 className="font-serif text-xl text-[#1F2421]">Edit Catering Requirements & Pax</h3>
          </div>
          <button
            onClick={onClose}
            className="text-[#8C877D] hover:text-[#1F2421] transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs flex items-center gap-2">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Guest Count Override */}
          <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Event Catering Guest Count (Pax) *
              </label>
              <span className="text-[11px] text-[#736F68]">
                Can override wedding project guest count
              </span>
            </div>
            <input
              type="number"
              min={1}
              required
              value={formData.guestCount}
              onChange={(e) => setFormData({ ...formData, guestCount: Number(e.target.value) })}
              className="w-full text-sm font-semibold p-2 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] focus:ring-1 focus:ring-[#9E7D3B]"
            />
          </div>

          {/* Flexible Dietary Breakdown */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Flexible Dietary Distribution (Pax)
              </label>
              <span className="text-[11px] text-[#736F68]">
                Sum: {totalDietary} / {formData.guestCount} Pax (Flexible estimates permitted)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-[#065F46]">
                  Vegetarian
                </span>
                <input
                  type="number"
                  min={0}
                  value={formData.vegCount}
                  onChange={(e) => setFormData({ ...formData, vegCount: Number(e.target.value) })}
                  className="w-full text-xs p-1.5 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>

              <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-[#991B1B]">
                  Non-Vegetarian
                </span>
                <input
                  type="number"
                  min={0}
                  value={formData.nonVegCount}
                  onChange={(e) => setFormData({ ...formData, nonVegCount: Number(e.target.value) })}
                  className="w-full text-xs p-1.5 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>

              <div className="p-3 bg-[#FAF8F5] border border-[#E5E0D8] space-y-1">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-[#9E7D3B]">
                  Strict Jain
                </span>
                <input
                  type="number"
                  min={0}
                  value={formData.jainCount}
                  onChange={(e) => setFormData({ ...formData, jainCount: Number(e.target.value) })}
                  className="w-full text-xs p-1.5 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-medium text-[#736F68]">
                Dietary & Allergy Notes (e.g. Nut allergies, Vegan counters, Halal prep)
              </label>
              <input
                type="text"
                value={formData.dietaryNotes}
                onChange={(e) => setFormData({ ...formData, dietaryNotes: e.target.value })}
                placeholder="Separate dedicated Jain prep kitchen, nut allergies noted..."
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
              />
            </div>
          </div>

          {/* Service Style & Timings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Service Style
              </label>
              <select
                value={formData.serviceStyle}
                onChange={(e) => setFormData({ ...formData, serviceStyle: e.target.value })}
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              >
                <option value="Silver Platter">Silver Platter (Royal Thali / Plated)</option>
                <option value="Royal Buffet">Grand Palace Buffet</option>
                <option value="Live Counters">Interactive Live Culinary Stalls</option>
                <option value="Floating Degustation">Floating Hors d'oeuvres & Degustation</option>
                <option value="Traditional Pangat">Traditional Pangat (Sit-down Baithak)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Service Timings
              </label>
              <input
                type="text"
                value={formData.serviceTimings}
                onChange={(e) => setFormData({ ...formData, serviceTimings: e.target.value })}
                placeholder="e.g. 7:30 PM - 11:30 PM"
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
          </div>

          {/* Cuisine Preferences & Location */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Cuisine Preferences
              </label>
              <input
                type="text"
                value={formData.cuisinePreferences}
                onChange={(e) => setFormData({ ...formData, cuisinePreferences: e.target.value })}
                placeholder="Mewari Royal, Mughlai, Awadhi, Modern Pan-Asian..."
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Venue / Dining Courtyard
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g. Zenana Mahal Courtyard, City Palace"
                className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
          </div>

          {/* Target Catering Budget */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
              Allocated Catering Budget (₹ INR)
            </label>
            <input
              type="number"
              min={0}
              step={1000}
              value={formData.budget}
              onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
              placeholder="e.g. 1500000"
              className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#E5E0D8]">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68] hover:bg-[#FAF8F5]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B] transition-colors"
            >
              {loading ? 'Saving...' : 'Save Requirements'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
