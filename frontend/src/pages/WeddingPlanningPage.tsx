import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { planningApi } from '../services/planningApi';
import { vendorApi, projectApi } from '../services/api';

type Item = Record<string, any>;
const sections = ['tasks', 'vendors', 'allocations', 'expenses', 'accommodations', 'logistics'] as const;
type Section = typeof sections[number];
const fields: Record<Section, string[]> = {
  tasks: ['title', 'description', 'category', 'priority', 'status', 'due_date', 'assigned_to', 'function_id'],
  vendors: ['vendor_id', 'function_id', 'category', 'responsibility', 'contract_amount', 'status'],
  allocations: ['category', 'amount', 'notes'],
  expenses: ['category', 'description', 'amount', 'expense_date', 'notes'],
  accommodations: ['hotel_name', 'room_type', 'room_count', 'nightly_rate', 'check_in', 'check_out', 'status', 'notes'],
  logistics: ['function_id', 'service_type', 'vehicle_type', 'vehicle_count', 'pickup_location', 'dropoff_location', 'scheduled_at', 'driver_contact', 'status', 'notes'],
};
const defaults: Record<string, string> = { priority: 'Medium', status: 'To Do', category: 'General', room_count: '1', vehicle_count: '1', amount: '0', contract_amount: '0', nightly_rate: '0' };
export function WeddingPlanningPage() {
  const { id = '' } = useParams();
  const [section, setSection] = useState<Section>('tasks');
  const [items, setItems] = useState<Item[]>([]);
  const [audit, setAudit] = useState<Item[]>([]);
  const [vendors, setVendors] = useState<Item[]>([]);
  const [staff, setStaff] = useState<Item[]>([]);
  const [functions, setFunctions] = useState<Item[]>([]);
  const [summary, setSummary] = useState<Item | null>(null);
  const [form, setForm] = useState<Item>({});
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    if (!id) return;
    setBusy(true);
    try { setItems(await planningApi.list(id, section)); setSummary(await planningApi.summary(id)); setAudit(await planningApi.audit(id)); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to load planning records'); }
    finally { setBusy(false); }
  };
  useEffect(() => { setForm({}); setEditing(null); void refresh(); }, [id, section]);
  useEffect(() => { if (id) projectApi.get(id).then((project: any) => setFunctions(project.functions || [])).catch(() => setFunctions([])); }, [id]);
  useEffect(() => { if (id) planningApi.staff(id).then(setStaff).catch(() => setStaff([])); }, [id]);
  useEffect(() => { vendorApi.list({isActive: true}).then((result: any) => setVendors(result.items || [])).catch(() => setVendors([])); }, []);
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: Item = {};
      fields[section].forEach(key => { const value = form[key] ?? defaults[key]; if (value !== undefined && value !== '') payload[key] = value; });
      if (section === 'vendors' && payload.category === 'General') payload.category = 'Other';
      if (!editing && section !== 'tasks' && payload.status === 'To Do') payload.status = ({vendors:'Proposed',accommodations:'Tentative',logistics:'Planned'} as Record<string,string>)[section] || payload.status;
      if (editing) await planningApi.update(id, section, editing, payload);
      else await planningApi.create(id, section, payload);
      setForm({}); setEditing(null); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : 'Save failed'); }
  };
  const remove = async (recordId: string) => {
    if (!window.confirm('Delete this planning record?')) return;
    try { await planningApi.remove(id, section, recordId); await refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Delete failed'); }
  };
  return <main className="p-6 space-y-6 max-w-7xl mx-auto">
    <header><Link to={`/projects/${id}`} className="text-sm text-amber-700">Back to wedding dossier</Link><h1 className="text-3xl font-semibold mt-2">Wedding Planning Command Center</h1><p className="text-slate-500">Tasks, suppliers, budgets, guest stays and transport for this wedding.</p></header>
    {summary && <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{(['estimated_budget','allocated','committed','spent','remaining_budget','uncommitted_budget'] as const).map(key => <div key={key} className="rounded-lg border bg-white p-4"><div className="text-xs uppercase text-slate-500">{key.replaceAll('_',' ')}</div><div className="text-lg font-semibold">ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¹{Number(summary[key] || 0).toLocaleString('en-IN')}</div></div>)}</div>}
    <nav className="flex gap-2 flex-wrap" aria-label="Planning sections">{sections.map(s => <button key={s} onClick={() => setSection(s)} className={`rounded-lg px-4 py-2 border capitalize ${section === s ? 'bg-amber-900 text-white' : 'bg-white text-slate-700'}`}>{s}</button>)}</nav>
    {error && <div role="alert" className="text-red-700 border border-red-200 p-3 rounded">{error}</div>}
    <section className="rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold capitalize mb-4">{editing ? 'Edit' : 'Add'} {section === 'tasks' ? 'task' : section.slice(0, -1)}</h2>
      <form onSubmit={save} className="grid md:grid-cols-3 gap-3">{fields[section].map(key => <label key={key} className="text-sm capitalize">{key.replaceAll('_',' ')}{key === "function_id" ? <select className="block w-full border rounded p-2 mt-1" value={form[key] ?? ""} onChange={e => setForm(previous => ({...previous,[key]:e.target.value}))}><option value="">All functions</option>{functions.map(fn => <option key={fn.id} value={fn.id}>{fn.functionName}</option>)}</select> : key === "assigned_to" ? <select className="block w-full border rounded p-2 mt-1" value={form[key] ?? ""} onChange={e => setForm(previous => ({...previous,[key]:e.target.value}))}><option value="">Unassigned</option>{staff.map(member => <option key={member.id} value={member.id}>{member.label}</option>)}</select> : key === "vendor_id" ? <select className="block w-full border rounded p-2 mt-1" value={form[key] ?? ""} onChange={e => setForm(previous => ({...previous,[key]:e.target.value}))}><option value="">Select vendor</option>{vendors.map(v => <option key={v.id} value={v.id}>{v.name} ({v.category})</option>)}</select> : <input className="block w-full border rounded p-2 mt-1" type={key.includes('date') || key === 'due_date' || key === 'check_in' || key === 'check_out' ? 'date' : key === 'scheduled_at' ? 'datetime-local' : ['amount','contract_amount','nightly_rate','room_count','vehicle_count'].includes(key) ? 'number' : 'text'} min={['amount','contract_amount','nightly_rate','room_count','vehicle_count'].includes(key) ? '0' : undefined} step={['amount','contract_amount','nightly_rate'].includes(key) ? '0.01' : undefined} value={form[key] ?? defaults[key] ?? ''} onChange={e => setForm(previous => ({...previous,[key]:e.target.value}))}/>}</label>)}<div className="flex items-end gap-2"><button type="submit" className="bg-amber-900 text-white rounded px-5 py-2">{editing ? 'Save changes' : 'Add record'}</button>{editing && <button type="button" onClick={() => {setEditing(null);setForm({});}} className="border rounded px-4 py-2">Cancel</button>}</div></form>
    </section>
    <section className="rounded-xl border bg-white overflow-x-auto"><table className="min-w-full text-sm"><thead><tr className="bg-slate-100">{fields[section].map(key => <th key={key} className="p-3 text-left capitalize">{key.replaceAll('_',' ')}</th>)}<th className="p-3">Actions</th></tr></thead><tbody>{items.map(item => <tr key={item.id} className="border-t">{fields[section].map(key => <td key={key} className="p-3">{String(item[key] ?? 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â')}</td>)}<td className="p-3 whitespace-nowrap"><button className="text-amber-800 mr-3" onClick={() => {setEditing(item.id);setForm(item);}}>Edit</button><button className="text-red-700" onClick={() => void remove(item.id)}>Delete</button></td></tr>)}</tbody></table>{!busy && !items.length && <p className="p-5 text-slate-500">No records yet. Add the first one above.</p>}{busy && <p className="p-5">LoadingÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦</p>}</section>
    <section className="border rounded-xl bg-white p-5"><h2 className="text-lg font-semibold mb-3">Planning activity</h2><div className="max-h-48 overflow-auto space-y-2">{audit.map(entry => <p key={entry.id} className="text-xs text-slate-600">{entry.action} Ãƒâ€šÃ‚Â· {entry.resource_type} Ãƒâ€šÃ‚Â· {entry.created_at}</p>)}{audit.length === 0 && <p className="text-sm text-slate-500">No recorded activity yet.</p>}</div></section>
  </main>;
}
