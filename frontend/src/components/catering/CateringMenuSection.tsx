import React, { useState, useEffect } from 'react';
import { 
  UtensilsCrossed, 
  Plus, 
  Trash2, 
  Edit2, 
  Sparkles, 
  ChefHat, 
  X
} from 'lucide-react';
import { CateringPlan, CateringMenuItem, PresetSummary } from '../../types/catering';
import { cateringApi } from '../../services/api';

interface CateringMenuSectionProps {
  plan: CateringPlan;
  onUpdate: () => void;
}

const COURSE_CATEGORIES = [
  'Welcome Beverages & Sharbat',
  'Starters & Canapés',
  'Royal Live Stations',
  'Mains',
  'Artisanal Breads & Rice',
  'Palace Confections & Desserts',
  'Paan & Digestifs',
];

const DIETARY_TAGS = [
  'Vegetarian',
  'Non-Vegetarian',
  'Jain',
  'Vegan',
  'Gluten-Free',
  'Contains Nuts',
  'Halal',
];

export const CateringMenuSection: React.FC<CateringMenuSectionProps> = ({ plan, onUpdate }) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isPresetModalOpen, setIsPresetModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CateringMenuItem | null>(null);

  // Add/Edit Dish state
  const [dishName, setDishName] = useState('');
  const [dishDescription, setDishDescription] = useState('');
  const [courseCategory, setCourseCategory] = useState(COURSE_CATEGORIES[1]);
  const [dietaryTag, setDietaryTag] = useState(DIETARY_TAGS[0]);
  const [quantityNote, setQuantityNote] = useState('');
  const [itemError, setItemError] = useState<string | null>(null);
  const [itemLoading, setItemLoading] = useState(false);

  // Preset state
  const [presets, setPresets] = useState<PresetSummary[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('');
  const [presetMode, setPresetMode] = useState<'append' | 'replace'>('append');
  const [presetLoading, setPresetLoading] = useState(false);
  const [presetError, setPresetError] = useState<string | null>(null);

  useEffect(() => {
    cateringApi.listPresets().then(setPresets).catch(() => {});
  }, []);

  const openAddDish = () => {
    setEditingItem(null);
    setDishName('');
    setDishDescription('');
    setCourseCategory(COURSE_CATEGORIES[1]);
    setDietaryTag(DIETARY_TAGS[0]);
    setQuantityNote('');
    setItemError(null);
    setIsAddModalOpen(true);
  };

  const openEditDish = (item: CateringMenuItem) => {
    setEditingItem(item);
    setDishName(item.itemName);
    setDishDescription(item.description || '');
    setCourseCategory(item.courseCategory);
    setDietaryTag(item.dietaryTag);
    setQuantityNote(item.quantityNote || '');
    setItemError(null);
    setIsAddModalOpen(true);
  };

  const handleSaveDish = async (e: React.FormEvent) => {
    e.preventDefault();
    setItemLoading(true);
    setItemError(null);

    try {
      if (editingItem) {
        await cateringApi.updateMenuItem(plan.id, editingItem.id, {
          itemName: dishName,
          description: dishDescription || null,
          courseCategory,
          dietaryTag,
          quantityNote: quantityNote || null,
        });
      } else {
        await cateringApi.createMenuItem(plan.id, {
          itemName: dishName,
          description: dishDescription || null,
          courseCategory,
          dietaryTag,
          quantityNote: quantityNote || null,
        });
      }
      setIsAddModalOpen(false);
      onUpdate();
    } catch (err: any) {
      setItemError(err.message || 'Failed to save menu dish.');
    } finally {
      setItemLoading(false);
    }
  };

  const handleDeleteDish = async (itemId: string) => {
    if (!window.confirm('Remove this dish from the menu?')) return;
    try {
      await cateringApi.deleteMenuItem(plan.id, itemId);
      onUpdate();
    } catch (err: any) {
      alert(err.message || 'Failed to delete dish.');
    }
  };

  const handleApplyPreset = async () => {
    if (!selectedPresetId) return;
    setPresetLoading(true);
    setPresetError(null);

    try {
      await cateringApi.applyPreset(plan.id, selectedPresetId, presetMode);
      setIsPresetModalOpen(false);
      onUpdate();
    } catch (err: any) {
      setPresetError(err.message || 'Failed to apply preset.');
    } finally {
      setPresetLoading(false);
    }
  };

  // Group items by course
  const groupedItems: Record<string, CateringMenuItem[]> = {};
  plan.menuItems.forEach((item) => {
    if (!groupedItems[item.courseCategory]) {
      groupedItems[item.courseCategory] = [];
    }
    groupedItems[item.courseCategory].push(item);
  });

  const getDietaryBadgeClass = (tag: string) => {
    switch (tag) {
      case 'Vegetarian':
        return 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]';
      case 'Non-Vegetarian':
        return 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]';
      case 'Jain':
        return 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]';
      case 'Vegan':
        return 'bg-[#F0FDF4] text-[#166534] border-[#BBF7D0]';
      default:
        return 'bg-[#FAF8F5] text-[#1F2421] border-[#E5E0D8]';
    }
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
      {/* Header & Preset Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E0D8]">
        <div>
          <div className="flex items-center gap-2">
            <UtensilsCrossed size={18} className="text-[#9E7D3B]" />
            <h3 className="font-serif text-xl text-[#1F2421]">Curated Event Menu</h3>
          </div>
          <p className="text-xs text-[#736F68] mt-1">
            {plan.menuItems.length} custom dishes across{' '}
            {Object.keys(groupedItems).length} royal courses
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              if (presets.length > 0 && !selectedPresetId) setSelectedPresetId(presets[0].id);
              setIsPresetModalOpen(true);
            }}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#FAF8F5] hover:bg-[#EFEBE4] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#1F2421] font-semibold transition-colors"
          >
            <Sparkles size={14} className="text-[#9E7D3B]" />
            <span>Apply Luxury Preset</span>
          </button>

          <button
            type="button"
            onClick={openAddDish}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#1F2421] hover:bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold transition-colors"
          >
            <Plus size={14} />
            <span>Add Dish</span>
          </button>
        </div>
      </div>

      {/* Empty State */}
      {plan.menuItems.length === 0 ? (
        <div className="text-center py-12 px-4 border border-dashed border-[#E5E0D8] bg-[#FAF8F5] space-y-3">
          <ChefHat size={36} className="mx-auto text-[#9E7D3B]" />
          <h4 className="font-serif text-lg text-[#1F2421]">No Menu Dishes Configured Yet</h4>
          <p className="text-xs text-[#736F68] max-w-md mx-auto">
            Build a bespoke degustation menu dish by dish, or apply one of our curated royal banquet templates (Mewari Feast, Sheesh Mahal, or Pan-Asian).
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <button
              onClick={() => {
                if (presets.length > 0 && !selectedPresetId) setSelectedPresetId(presets[0].id);
                setIsPresetModalOpen(true);
              }}
              className="px-4 py-2 bg-[#9E7D3B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#1F2421] transition-colors"
            >
              Browse Luxury Presets
            </button>
            <button
              onClick={openAddDish}
              className="px-4 py-2 border border-[#E5E0D8] bg-[#FFFFFF] text-xs uppercase tracking-wider font-semibold text-[#1F2421] hover:bg-[#FAF8F5]"
            >
              Add Custom Dish
            </button>
          </div>
        </div>
      ) : (
        /* Courses Accordion / Grouped List */
        <div className="space-y-6">
          {Object.entries(groupedItems).map(([category, items]) => (
            <div key={category} className="border border-[#E5E0D8] bg-[#FAF8F5]">
              <div className="px-4 py-2.5 bg-[#EFEBE4] border-b border-[#E5E0D8] flex items-center justify-between">
                <span className="font-serif text-sm font-semibold text-[#1F2421] tracking-wide">
                  {category}
                </span>
                <span className="text-[11px] text-[#736F68] font-medium">
                  {items.length} {items.length === 1 ? 'dish' : 'dishes'}
                </span>
              </div>

              <div className="divide-y divide-[#E5E0D8] bg-[#FFFFFF]">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#FAF8F5] transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-[#1F2421]">{item.itemName}</span>
                        <span
                          className={`text-[10px] uppercase tracking-wider px-2 py-0.5 border font-semibold ${getDietaryBadgeClass(
                            item.dietaryTag
                          )}`}
                        >
                          {item.dietaryTag}
                        </span>
                        {item.quantityNote && (
                          <span className="text-[11px] text-[#736F68] italic">
                            • {item.quantityNote}
                          </span>
                        )}
                      </div>
                      {item.description && (
                        <p className="text-xs text-[#736F68] leading-relaxed">{item.description}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <button
                        onClick={() => openEditDish(item)}
                        className="p-1.5 text-[#736F68] hover:text-[#1F2421] hover:bg-[#FAF8F5] rounded transition-colors"
                        title="Edit dish"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={() => handleDeleteDish(item.id)}
                        className="p-1.5 text-[#991B1B] hover:text-[#DC2626] hover:bg-[#FEF2F2] rounded transition-colors"
                        title="Delete dish"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Dish Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-lg p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <h3 className="font-serif text-lg text-[#1F2421]">
                {editingItem ? 'Edit Menu Dish' : 'Add Dish to Menu'}
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-[#8C877D]">
                <X size={18} />
              </button>
            </div>

            {itemError && (
              <div className="p-2.5 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs">
                {itemError}
              </div>
            )}

            <form onSubmit={handleSaveDish} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Dish / Culinary Item Name *
                </label>
                <input
                  type="text"
                  required
                  value={dishName}
                  onChange={(e) => setDishName(e.target.value)}
                  placeholder="e.g. Mewari Junglee Maas, Dum Biryani..."
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Course Category *
                  </label>
                  <select
                    value={courseCategory}
                    onChange={(e) => setCourseCategory(e.target.value)}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  >
                    {COURSE_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                    Dietary Classification *
                  </label>
                  <select
                    value={dietaryTag}
                    onChange={(e) => setDietaryTag(e.target.value)}
                    className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                  >
                    {DIETARY_TAGS.map((tag) => (
                      <option key={tag} value={tag}>
                        {tag}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Description & Ingredients
                </label>
                <textarea
                  rows={2}
                  value={dishDescription}
                  onChange={(e) => setDishDescription(e.target.value)}
                  placeholder="e.g. Slow-simmered tender lamb cooked in pure Mathania chili paste and ghee..."
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                  Serving / Portion Note (Optional)
                </label>
                <input
                  type="text"
                  value={quantityNote}
                  onChange={(e) => setQuantityNote(e.target.value)}
                  placeholder="e.g. Served in silver handi, 200g portion"
                  className="w-full text-xs p-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] mt-1"
                />
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
                  disabled={itemLoading}
                  className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
                >
                  {itemLoading ? 'Saving...' : editingItem ? 'Update Dish' : 'Add to Menu'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Apply Luxury Preset Modal */}
      {isPresetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-xl p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-[#9E7D3B]" />
                <h3 className="font-serif text-lg text-[#1F2421]">Apply Curated Luxury Menu Preset</h3>
              </div>
              <button onClick={() => setIsPresetModalOpen(false)} className="text-[#8C877D]">
                <X size={18} />
              </button>
            </div>

            {presetError && (
              <div className="p-2.5 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs">
                {presetError}
              </div>
            )}

            <div className="space-y-3">
              <label className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Select Luxury Banquet Template:
              </label>

              <div className="grid grid-cols-1 gap-2.5">
                {presets.map((p) => {
                  const isSelected = selectedPresetId === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedPresetId(p.id)}
                      className={`p-3 border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-[#9E7D3B] bg-[#FAF8F5] shadow-sm'
                          : 'border-[#E5E0D8] hover:border-[#9E7D3B]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-serif text-sm font-bold text-[#1F2421]">{p.name}</span>
                        <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-[#FFFFFF] border border-[#E5E0D8] font-semibold text-[#9E7D3B]">
                          {p.itemCount} Dishes
                        </span>
                      </div>
                      <p className="text-xs text-[#736F68] mt-1">{p.description}</p>
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        {Object.entries(p.courseBreakdown).map(([course, count]) => (
                          <span
                            key={course}
                            className="text-[10px] text-[#2B2D2F] bg-[#FFFFFF] px-1.5 py-0.5 border border-[#E5E0D8]"
                          >
                            {course}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Mode selection: Append vs Replace */}
            <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-3 space-y-2">
              <span className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider block">
                Application Mode
              </span>
              <div className="flex items-center gap-6 text-xs text-[#1F2421]">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="presetMode"
                    value="append"
                    checked={presetMode === 'append'}
                    onChange={() => setPresetMode('append')}
                  />
                  <span><b>Append:</b> Add preset dishes to existing menu</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="presetMode"
                    value="replace"
                    checked={presetMode === 'replace'}
                    onChange={() => setPresetMode('replace')}
                  />
                  <span><b>Replace:</b> Overwrite existing menu items</span>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
              <button
                type="button"
                onClick={() => setIsPresetModalOpen(false)}
                className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider font-semibold text-[#736F68]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={presetLoading || !selectedPresetId}
                onClick={handleApplyPreset}
                className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#9E7D3B]"
              >
                {presetLoading ? 'Applying...' : 'Apply Preset Template'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
