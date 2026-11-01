import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Plus, 
  Search, 
  Phone, 
  Mail, 
  MapPin, 
  Star, 
  Edit3, 
  CheckCircle2, 
  XCircle, 
  MessageSquare, 
  X, 
} from 'lucide-react';
import { Vendor } from '../types/catering';
import { vendorApi } from '../services/api';

const SERVICE_CATEGORIES = [
  'All',
  'Catering',
  'Decor & Production',
  'Photography & Cinematography',
  'Entertainment & Artists',
  'Hospitality & Logistics',
  'Bridal Styling & MUA',
  'Venues & Palaces',
];

const CITIES = ['All', 'Jaipur', 'Udaipur', 'Jodhpur', 'Delhi NCR', 'Mumbai'];

export const VendorsPage: React.FC = () => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedCity, setSelectedCity] = useState('All');
  const [isActiveOnly, setIsActiveOnly] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [contactPerson, setContactPerson] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [serviceCategory, setServiceCategory] = useState('Catering');
  const [city, setCity] = useState('Jaipur');
  const [address, setAddress] = useState('');
  const [rating, setRating] = useState<number | ''>(5.0);
  const [notes, setNotes] = useState('');

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const data = await vendorApi.list({
        search: search || undefined,
        category: selectedCategory !== 'All' ? selectedCategory : undefined,
        city: selectedCity !== 'All' ? selectedCity : undefined,
        isActive: isActiveOnly ? true : undefined,
      });
      setVendors(data);
    } catch (err: any) {
      console.error('Failed to load vendors', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [search, selectedCategory, selectedCity, isActiveOnly]);

  const openCreateModal = () => {
    setEditingVendor(null);
    setName('');
    setContactPerson('');
    setPhone('+91 ');
    setEmail('');
    setServiceCategory('Catering');
    setCity('Jaipur');
    setAddress('');
    setRating(5.0);
    setNotes('');
    setModalError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (vendor: Vendor) => {
    setEditingVendor(vendor);
    setName(vendor.name);
    setContactPerson(vendor.contactPerson || '');
    setPhone(vendor.phone);
    setEmail(vendor.email || '');
    setServiceCategory(vendor.serviceCategory);
    setCity(vendor.city);
    setAddress(vendor.address || '');
    setRating(vendor.rating !== null && vendor.rating !== undefined ? vendor.rating : '');
    setNotes(vendor.notes || '');
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleSubmitVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setModalError(null);

    const payload = {
      name,
      contactPerson: contactPerson || null,
      phone,
      email: email || null,
      serviceCategory,
      city,
      address: address || null,
      rating: rating === '' ? null : Number(rating),
      notes: notes || null,
    };

    try {
      if (editingVendor) {
        await vendorApi.update(editingVendor.id, payload);
      } else {
        await vendorApi.create(payload);
      }
      setIsModalOpen(false);
      fetchVendors();
    } catch (err: any) {
      setModalError(err.message || 'Failed to save vendor details.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleToggleActive = async (vendor: Vendor) => {
    if (
      !window.confirm(
        `Are you sure you want to ${vendor.isActive ? 'deactivate' : 'reactivate'} ${vendor.name}?`
      )
    ) {
      return;
    }

    try {
      if (vendor.isActive) {
        await vendorApi.delete(vendor.id);
      } else {
        await vendorApi.update(vendor.id, { isActive: true });
      }
      fetchVendors();
    } catch (err: any) {
      alert(err.message || 'Failed to update vendor status.');
    }
  };

  const cateringVendorsCount = vendors.filter((v) => v.serviceCategory === 'Catering').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E0D8]">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[#9E7D3B] text-xl font-serif">✦</span>
            <h1 className="font-serif text-2xl text-[#1F2421]">Vendor Partner Directory</h1>
          </div>
          <p className="text-xs text-[#736F68] mt-1">
            Centrally managed master vendor partners across Rajasthan & luxury destination hubs
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold transition-colors"
        >
          <Plus size={14} />
          <span>Register New Vendor</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold">
            Total Partners
          </span>
          <div className="font-serif text-2xl font-bold text-[#1F2421]">{vendors.length}</div>
        </div>
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold">
            Catering Caterers
          </span>
          <div className="font-serif text-2xl font-bold text-[#9E7D3B]">{cateringVendorsCount}</div>
        </div>
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold">
            Jaipur & Udaipur Network
          </span>
          <div className="font-serif text-2xl font-bold text-[#1F2421]">
            {vendors.filter((v) => ['Jaipur', 'Udaipur'].includes(v.city)).length}
          </div>
        </div>
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold">
            Active Verified
          </span>
          <div className="font-serif text-2xl font-bold text-[#10B981]">
            {vendors.filter((v) => v.isActive).length}
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex flex-col md:flex-row md:items-center gap-4 justify-between">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8C877D]" />
          <input
            type="text"
            placeholder="Search by vendor firm name or contact person..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-9 pr-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:ring-1 focus:ring-[#9E7D3B]"
          />
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] font-semibold"
          >
            {SERVICE_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                Category: {cat}
              </option>
            ))}
          </select>

          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] font-semibold"
          >
            {CITIES.map((c) => (
              <option key={c} value={c}>
                City: {c}
              </option>
            ))}
          </select>

          <label className="flex items-center gap-1.5 text-xs text-[#1F2421] cursor-pointer">
            <input
              type="checkbox"
              checked={isActiveOnly}
              onChange={(e) => setIsActiveOnly(e.target.checked)}
            />
            <span>Active only</span>
          </label>
        </div>
      </div>

      {/* Vendors Cards Grid */}
      {loading ? (
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center text-xs text-[#736F68]">
          Loading vendor directory...
        </div>
      ) : vendors.length === 0 ? (
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center space-y-3">
          <Building2 size={36} className="mx-auto text-[#8C877D]" />
          <h3 className="font-serif text-lg text-[#1F2421]">No Vendors Found</h3>
          <p className="text-xs text-[#736F68] max-w-sm mx-auto">
            No vendor partners match the current search filters. Register a new vendor partner or reset filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {vendors.map((vendor) => (
            <div
              key={vendor.id}
              className={`border p-5 space-y-4 transition-all bg-[#FFFFFF] ${
                vendor.isActive
                  ? 'border-[#E5E0D8] hover:border-[#9E7D3B] hover:shadow-sm'
                  : 'border-[#E5E0D8] bg-[#FAF8F5] opacity-60'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 pb-3 border-b border-[#E5E0D8]">
                <div className="space-y-0.5">
                  <h3 className="font-serif text-base font-bold text-[#1F2421]">{vendor.name}</h3>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] font-semibold text-[#9E7D3B]">
                    {vendor.serviceCategory}
                  </span>
                </div>

                {vendor.rating && (
                  <div className="flex items-center gap-1 px-2 py-0.5 bg-[#FFFDF9] border border-[#FDE68A] text-[#B45309] text-xs font-bold">
                    <Star size={11} className="fill-current text-[#F59E0B]" />
                    <span>{vendor.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>

              {/* Contact Info */}
              <div className="space-y-1.5 text-xs text-[#736F68]">
                {vendor.contactPerson && (
                  <div className="font-medium text-[#1F2421]">
                    Liaison: {vendor.contactPerson}
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <Phone size={12} className="text-[#9E7D3B]" />
                  <span>{vendor.phone}</span>
                </div>
                {vendor.email && (
                  <div className="flex items-center gap-1.5">
                    <Mail size={12} className="text-[#9E7D3B]" />
                    <span className="truncate">{vendor.email}</span>
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <MapPin size={12} className="text-[#9E7D3B]" />
                  <span>{vendor.city} {vendor.address ? `• ${vendor.address}` : ''}</span>
                </div>
              </div>

              {vendor.notes && (
                <p className="text-[11px] text-[#736F68] italic line-clamp-2 bg-[#FAF8F5] p-2 border border-[#E5E0D8]">
                  "{vendor.notes}"
                </p>
              )}

              {/* Actions Footer */}
              <div className="pt-3 border-t border-[#E5E0D8] flex items-center justify-between text-xs">
                <a
                  href={`https://wa.me/${vendor.phone.replace(/[^0-9]/g, '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[#10B981] hover:underline font-medium"
                >
                  <MessageSquare size={12} />
                  <span>WhatsApp</span>
                </a>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditModal(vendor)}
                    className="p-1.5 text-[#736F68] hover:text-[#1F2421] hover:bg-[#FAF8F5] rounded"
                    title="Edit Vendor"
                  >
                    <Edit3 size={13} />
                  </button>
                  <button
                    onClick={() => handleToggleActive(vendor)}
                    className={`p-1.5 rounded ${
                      vendor.isActive
                        ? 'text-[#991B1B] hover:bg-[#FEF2F2]'
                        : 'text-[#10B981] hover:bg-[#ECFDF5]'
                    }`}
                    title={vendor.isActive ? 'Deactivate' : 'Reactivate'}
                  >
                    {vendor.isActive ? <XCircle size={13} /> : <CheckCircle2 size={13} />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Register / Edit Vendor Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-lg my-8 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <Building2 size={18} className="text-[#9E7D3B]" />
                <h3 className="font-serif text-lg text-[#1F2421]">
                  {editingVendor ? 'Edit Vendor Dossier' : 'Register Luxury Vendor Partner'}
                </h3>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-[#8C877D]">
                <X size={18} />
              </button>
            </div>

            {modalError && (
              <div className="p-2.5 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleSubmitVendor} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Vendor Partner Firm Name *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Royal Udaipur Grand Caterers"
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Service Category *
                  </label>
                  <select
                    value={serviceCategory}
                    onChange={(e) => setServiceCategory(e.target.value)}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  >
                    {SERVICE_CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Operating City *
                  </label>
                  <input
                    type="text"
                    required
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="Jaipur, Udaipur, Jodhpur..."
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Contact Person / Liaison
                  </label>
                  <input
                    type="text"
                    value={contactPerson}
                    onChange={(e) => setContactPerson(e.target.value)}
                    placeholder="e.g. Maharaj Vikram Singh"
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    WhatsApp Phone *
                  </label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="concierge@caterer.in"
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Partner Rating (0.0 - 5.0)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    step={0.1}
                    value={rating}
                    onChange={(e) => setRating(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Physical Kitchen / Office Address
                </label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g. MI Road, Jaipur"
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Specialties & Notes
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Specializes in Mewari royal cuisine, silver banquet service, live tandoor stations..."
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
                >
                  {modalLoading ? 'Saving...' : editingVendor ? 'Update Partner' : 'Register Vendor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
