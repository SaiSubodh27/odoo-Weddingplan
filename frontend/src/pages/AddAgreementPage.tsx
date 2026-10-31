import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Save, 
  Calendar, 
  Users, 
  DollarSign, 
  Plus, 
  Trash2
} from 'lucide-react';
import { agreementApi } from '../services/api';
import { useClients } from '../context/ClientContext';

export const AddAgreementPage: React.FC = () => {
  const navigate = useNavigate();
  const { clients } = useClients();

  // Form State
  const [selectedClientId, setSelectedClientId] = useState('');
  const [weddingDate, setWeddingDate] = useState('');
  const [weddingLocation, setWeddingLocation] = useState('Udaipur, Rajasthan');
  const [venue, setVenue] = useState('The Oberoi Udaivilas');
  const [guestCount, setGuestCount] = useState(200);
  const [servicePackage, setServicePackage] = useState('Royal Palace Grandeur');

  // Multi-event functions
  const [functions, setFunctions] = useState([
    { name: 'Mehendi & High Tea', date: '', venue: 'Lakeside Courtyard', guest_count: 150, notes: 'Rajasthani folk performers and floral arches' },
    { name: 'Grand Sangeet Night', date: '', venue: 'Palace Ballroom', guest_count: 200, notes: 'Concert stage, royal lighting, and cocktail bar' },
    { name: 'Royal Phera & Mandap', date: '', venue: 'Floating Lake Mandap', guest_count: 200, notes: 'Traditional Shehnai, elephant welcome, rose petal shower' }
  ]);

  // Pricing
  const [packagePrice, setPackagePrice] = useState(2500000); // 25 Lakhs
  const [taxPercentage, setTaxPercentage] = useState(18);
  const [discountAmount, setDiscountAmount] = useState(100000); // 1 Lakh

  // Auto-calculated totals
  const taxAmount = (packagePrice * (taxPercentage / 100));
  const totalAmount = packagePrice + taxAmount - discountAmount;

  // Staged Milestones
  const [milestones, setMilestones] = useState([
    { name: '1. Advance Booking Retainer (25%)', percentage: 25, amount: 0, due_date: '', description: 'Secures wedding date and principal planner reservation' },
    { name: '2. Heritage Venue & Production Hold (40%)', percentage: 40, amount: 0, due_date: '', description: 'Palace vendor contracts and production advance' },
    { name: '3. Pre-Wedding Final Balance (35%)', percentage: 35, amount: 0, due_date: '', description: 'Final logistics, artist settlement, and on-ground ops' }
  ]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Recalculate milestone amounts when total changes
  useEffect(() => {
    setMilestones(prev => prev.map(m => ({
      ...m,
      amount: Math.round((totalAmount * (m.percentage / 100)) * 100) / 100
    })));
  }, [packagePrice, taxPercentage, discountAmount]);

  // Autofill from selected client
  const handleClientSelect = (clientId: string) => {
    setSelectedClientId(clientId);
    const client = clients.find(c => c.id === clientId);
    if (client) {
      if (client.weddingDate) {
        setWeddingDate(client.weddingDate);
        setFunctions(f => f.map(item => ({ ...item, date: client.weddingDate })));
      }
      if (client.weddingLocation) setWeddingLocation(client.weddingLocation);
      if (client.expectedGuestCount) setGuestCount(client.expectedGuestCount);
      if (client.servicePackage) setServicePackage(client.servicePackage);
    }
  };

  const handleAddFunction = () => {
    setFunctions([...functions, { name: 'Post-Wedding Brunch', date: weddingDate, venue: 'Palace Terrace', guest_count: guestCount, notes: '' }]);
  };

  const handleRemoveFunction = (index: number) => {
    setFunctions(functions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientId) {
      setError('Please select an existing registered client.');
      return;
    }
    if (!weddingDate) {
      setError('Please specify the wedding date.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        client_id: selectedClientId,
        wedding_date: weddingDate,
        wedding_location: weddingLocation,
        venue,
        guest_count: Number(guestCount),
        wedding_functions: functions,
        service_package: servicePackage,
        included_services: [
          'Full-scale luxury destination wedding planning and design',
          'Heritage palace venue liaison and permissions',
          'Celebrity artist booking and royal folk entertainment',
          'Bespoke decor, floral architecture, and mood lighting',
          'Guest logistics, royal vintage car convoys, and 24/7 concierge'
        ],
        excluded_services: [
          'Direct palace accommodation tariffs beyond negotiated inventory',
          'Direct catering food & liquor bills (settled directly with hotel)',
          'Personal bridal designer couture and jewelry purchases'
        ],
        package_price: packagePrice,
        tax_percentage: taxPercentage,
        discount_amount: discountAmount,
        milestones: milestones.map(m => ({
          name: m.name,
          percentage: m.percentage,
          amount: m.amount,
          due_date: m.due_date || weddingDate,
          description: m.description
        })),
        created_by: 'Maharani Gayatri Singh'
      };

      const res = await agreementApi.create(payload);
      // Auto-generate initial PDF for preview
      await agreementApi.generatePdf(res.id).catch(() => null);
      navigate(`/agreements/${res.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create service agreement.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
        <button
          onClick={() => navigate('/agreements')}
          className="inline-flex items-center gap-1.5 text-xs uppercase tracking-widest text-[#736F68] hover:text-[#1F2421]"
        >
          <ArrowLeft size={14} /> Back to Agreements
        </button>
        <span className="text-[10px] uppercase tracking-widest text-[#9E7D3B] font-medium">
          Dossier Preparation
        </span>
      </div>

      {/* Header */}
      <div>
        <h1 className="font-serif text-3xl text-[#1F2421]">Prepare Bespoke Service Agreement</h1>
        <p className="text-xs text-[#736F68] mt-1">
          Draft legally compliant wedding planning agreement, multi-event schedules, and staged payment schedules.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section A: Registered Client Selection */}
        <div className="bg-white border border-[#E5E0D8] p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
            <Users size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-lg font-semibold text-[#1F2421]">Section A — Registered Client Dossier</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Select Registered Client *
              </label>
              <select
                value={selectedClientId}
                onChange={(e) => handleClientSelect(e.target.value)}
                required
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B] bg-white text-[#1F2421]"
              >
                <option value="">-- Choose Existing Client Record --</option>
                {clients.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.partner1Name} & {c.partner2Name} ({c.id} · {c.email})
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-[#8C877D] mt-1">
                Phase 2 reuses registered client records. Never duplicate client dossiers.
              </p>
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Service Package Tier
              </label>
              <input
                type="text"
                value={servicePackage}
                onChange={(e) => setServicePackage(e.target.value)}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>
          </div>
        </div>

        {/* Section B: Wedding Parameters & Multiple Functions */}
        <div className="bg-white border border-[#E5E0D8] p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
            <Calendar size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-lg font-semibold text-[#1F2421]">Section B — Wedding & Multi-Event Ceremonies</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Primary Wedding Date *
              </label>
              <input
                type="date"
                value={weddingDate}
                onChange={(e) => setWeddingDate(e.target.value)}
                required
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Destination City
              </label>
              <input
                type="text"
                value={weddingLocation}
                onChange={(e) => setWeddingLocation(e.target.value)}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Heritage Venue / Estate
              </label>
              <input
                type="text"
                value={venue}
                onChange={(e) => setVenue(e.target.value)}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Estimated Guest Count
              </label>
              <input
                type="number"
                value={guestCount}
                onChange={(e) => setGuestCount(Number(e.target.value))}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>
          </div>

          {/* Planned Ceremonies */}
          <div className="pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#1F2421]">Planned Functions Schedule</span>
              <button
                type="button"
                onClick={handleAddFunction}
                className="text-[11px] text-[#9E7D3B] hover:underline inline-flex items-center gap-1 font-medium"
              >
                <Plus size={12} /> Add Ceremony
              </button>
            </div>

            <div className="space-y-2">
              {functions.map((fn, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 bg-[#FAF8F5] p-2.5 border border-[#E5E0D8] items-center text-xs">
                  <div className="col-span-3">
                    <input
                      type="text"
                      placeholder="Ceremony Name"
                      value={fn.name}
                      onChange={(e) => {
                        const copy = [...functions];
                        copy[idx].name = e.target.value;
                        setFunctions(copy);
                      }}
                      className="w-full border border-[#E5E0D8] p-1.5 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="date"
                      value={fn.date}
                      onChange={(e) => {
                        const copy = [...functions];
                        copy[idx].date = e.target.value;
                        setFunctions(copy);
                      }}
                      className="w-full border border-[#E5E0D8] p-1.5 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-3">
                    <input
                      type="text"
                      placeholder="Specific Hall / Lawn"
                      value={fn.venue}
                      onChange={(e) => {
                        const copy = [...functions];
                        copy[idx].venue = e.target.value;
                        setFunctions(copy);
                      }}
                      className="w-full border border-[#E5E0D8] p-1.5 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-3">
                    <input
                      type="text"
                      placeholder="Notes / Decor Theme"
                      value={fn.notes}
                      onChange={(e) => {
                        const copy = [...functions];
                        copy[idx].notes = e.target.value;
                        setFunctions(copy);
                      }}
                      className="w-full border border-[#E5E0D8] p-1.5 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-1 text-right">
                    <button
                      type="button"
                      onClick={() => handleRemoveFunction(idx)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section C: Commercial Pricing & Payment Schedule */}
        <div className="bg-white border border-[#E5E0D8] p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E5E0D8]">
            <DollarSign size={16} className="text-[#9E7D3B]" />
            <h2 className="font-serif text-lg font-semibold text-[#1F2421]">Section C — Commercial Terms & Staged Milestones</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Agreed Agency Fee (INR) *
              </label>
              <input
                type="number"
                value={packagePrice}
                onChange={(e) => setPackagePrice(Number(e.target.value))}
                required
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Applicable GST (%)
              </label>
              <input
                type="number"
                value={taxPercentage}
                onChange={(e) => setTaxPercentage(Number(e.target.value))}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold mb-1">
                Courtesy Discount (INR)
              </label>
              <input
                type="number"
                value={discountAmount}
                onChange={(e) => setDiscountAmount(Number(e.target.value))}
                className="w-full border border-[#E5E0D8] text-xs p-2.5 focus:outline-none focus:border-[#9E7D3B]"
              />
            </div>
          </div>

          {/* Total Summary */}
          <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-4 flex items-center justify-between text-xs">
            <div>
              <span className="text-[#8C877D]">Tax Breakdown:</span>
              <span className="font-semibold text-[#1F2421] ml-2">₹ {taxAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="text-base font-serif font-bold text-[#1F2421]">
              Total Contract Value: <span className="text-[#9E7D3B]">₹ {totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} INR</span>
            </div>
          </div>

          {/* Milestones */}
          <div className="pt-3">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#1F2421] block mb-2">
              Agreed Payment Milestones (Reconciled with Total)
            </span>
            <div className="space-y-2">
              {milestones.map((ms, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-3 bg-[#FFFFFF] p-3 border border-[#E5E0D8] items-center text-xs">
                  <div className="col-span-5">
                    <span className="font-medium text-[#1F2421] block">{ms.name}</span>
                    <span className="text-[10px] text-[#8C877D]">{ms.description}</span>
                  </div>
                  <div className="col-span-2 text-center font-mono">
                    {ms.percentage}%
                  </div>
                  <div className="col-span-2 font-semibold text-[#1F2421]">
                    ₹ {ms.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="col-span-3">
                    <input
                      type="date"
                      value={ms.due_date}
                      onChange={(e) => {
                        const copy = [...milestones];
                        copy[idx].due_date = e.target.value;
                        setMilestones(copy);
                      }}
                      className="w-full border border-[#E5E0D8] p-1.5 text-xs bg-white"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#E5E0D8]">
          <button
            type="button"
            onClick={() => navigate('/agreements')}
            className="px-5 py-2.5 border border-[#E5E0D8] text-xs uppercase tracking-wider font-medium text-[#736F68] hover:text-[#1F2421]"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-[#1F2421] hover:bg-[#343B37] text-white text-xs uppercase tracking-widest font-medium transition-colors shadow-sm inline-flex items-center gap-2"
          >
            <Save size={14} />
            {saving ? 'Creating Dossier...' : 'Save Draft & Generate PDF'}
          </button>
        </div>
      </form>
    </div>
  );
};
