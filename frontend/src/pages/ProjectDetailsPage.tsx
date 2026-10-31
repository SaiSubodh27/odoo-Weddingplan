import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Sparkles, 
  Calendar, 
  MapPin, 
  Users, 
  Banknote, 
  Clock, 
  CheckCircle2, 
  Plus, 
  Trash2, 
  Edit3, 
  AlertTriangle,
  History,
  Building2,
  Heart,
  X,
  CheckCircle,
  ExternalLink,
  IndianRupee
} from 'lucide-react';
import { projectApi } from '../services/api';
import { 
  WeddingProject, 
  WeddingFunction, 
  ProjectMilestone, 
  ProjectStatus, 
  FunctionStatus, 
  MilestoneStatus 
} from '../types/project';
import { getProjectStatusStyle } from './ProjectsPage';

export const ProjectDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<WeddingProject | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'functions' | 'milestones' | 'history'>('overview');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Modals state
  const [isEditProjectOpen, setIsEditProjectOpen] = useState<boolean>(false);
  const [isAddFunctionOpen, setIsAddFunctionOpen] = useState<boolean>(false);
  const [editingFunction, setEditingFunction] = useState<WeddingFunction | null>(null);
  const [isAddMilestoneOpen, setIsAddMilestoneOpen] = useState<boolean>(false);

  // Status Change Prompt
  const [isStatusModalOpen, setIsStatusModalOpen] = useState<boolean>(false);
  const [targetStatus, setTargetStatus] = useState<ProjectStatus>('Planning');
  const [statusNotes, setStatusNotes] = useState<string>('');

  const fetchProjectDetails = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await projectApi.get(id);
      setProject(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectDetails();
  }, [id]);

  const handleStatusChangeRequest = (newStatus: ProjectStatus) => {
    setTargetStatus(newStatus);
    setStatusNotes('');
    setIsStatusModalOpen(true);
  };

  const handleConfirmStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!project) return;

    try {
      await projectApi.updateStatus(
        project.id,
        targetStatus,
        'Maharani Gayatri Singh',
        statusNotes.trim() || undefined
      );
      setStatusMessage(`Project status updated to '${targetStatus}'.`);
      setTimeout(() => setStatusMessage(null), 3500);
      setIsStatusModalOpen(false);
      fetchProjectDetails();
    } catch (err: any) {
      alert(err.message || 'Failed to update project status.');
    }
  };

  // Milestone Toggle
  const handleToggleMilestone = async (ms: ProjectMilestone) => {
    if (!project) return;
    const newStatus: MilestoneStatus = ms.status === 'Completed' ? 'Pending' : 'Completed';

    try {
      await projectApi.updateMilestone(project.id, ms.id, { status: newStatus });
      fetchProjectDetails();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle milestone.');
    }
  };

  const handleDeleteMilestone = async (msId: string) => {
    if (!project || !window.confirm('Are you sure you want to remove this milestone checkpoint?')) return;
    try {
      await projectApi.deleteMilestone(project.id, msId);
      fetchProjectDetails();
    } catch (err: any) {
      alert(err.message || 'Failed to delete milestone.');
    }
  };

  const handleDeleteFunction = async (funcId: string) => {
    if (!project || !window.confirm('Are you sure you want to delete this wedding function?')) return;
    try {
      await projectApi.deleteFunction(project.id, funcId);
      fetchProjectDetails();
    } catch (err: any) {
      alert(err.message || 'Failed to delete function.');
    }
  };

  if (loading) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center text-xs text-[#736F68]">
        Loading wedding project dossier...
      </div>
    );
  }

  if (!project) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center max-w-lg mx-auto space-y-4">
        <h2 className="font-serif text-2xl text-[#1F2421]">Project Not Located</h2>
        <p className="text-xs text-[#736F68]">
          The project reference "{id}" could not be retrieved from the operational database.
        </p>
        <Link
          to="/projects"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold"
        >
          <ArrowLeft size={14} />
          <span>Back to Projects Directory</span>
        </Link>
      </div>
    );
  }

  const completedMilestones = project.milestones.filter(m => m.status === 'Completed').length;
  const totalMilestones = project.milestones.length;
  const milestoneProgress = totalMilestones > 0 ? Math.round((completedMilestones / totalMilestones) * 100) : 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Navigation & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="p-2 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] text-[#1F2421] transition-colors"
            title="Back to Projects"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-semibold">
              <span>{project.projectCode}</span>
              <span>·</span>
              <span>{project.location}</span>
            </div>
            <h1 className="font-serif text-3xl text-[#1F2421]">
              {project.projectName}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className={`px-2.5 py-1 text-[10px] uppercase tracking-wider font-semibold border ${getProjectStatusStyle(project.status)}`}>
            {project.status}
          </span>

          {/* Status Badge & Transition Selector */}
          <div className="flex items-center gap-2 border border-[#E5E0D8] bg-[#FFFFFF] px-3 py-1.5">
            <span className="text-[10px] uppercase tracking-wider text-[#736F68] font-semibold">Status:</span>
            <select
              value={project.status}
              onChange={(e) => handleStatusChangeRequest(e.target.value as ProjectStatus)}
              className="text-xs font-semibold bg-transparent border-none text-[#1F2421] focus:ring-0 cursor-pointer"
            >
              <option value="Planning">Planning</option>
              <option value="In Progress">In Progress</option>
              <option value="On Hold">On Hold</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>

          <button
            onClick={() => setIsEditProjectOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#FFFFFF] hover:bg-[#FAF8F5] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#1F2421] font-semibold transition-colors"
          >
            <Edit3 size={13} className="text-[#9E7D3B]" />
            <span>Edit Project</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-[#ECFDF5] border border-[#A7F3D0] text-xs font-semibold text-[#065F46] uppercase tracking-wider flex items-center gap-2">
          <CheckCircle size={15} />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-[#E5E0D8]">
        {[
          { key: 'overview', label: 'Overview & Specs', icon: Building2 },
          { key: 'functions', label: `Wedding Functions (${project.functions.length})`, icon: Calendar },
          { key: 'milestones', label: `Milestones (${completedMilestones}/${totalMilestones})`, icon: CheckCircle2 },
          { key: 'history', label: `Status History (${project.statusHistory.length})`, icon: History },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-3 text-xs uppercase tracking-wider font-semibold border-b-2 transition-colors ${
                isActive
                  ? 'border-[#1F2421] text-[#1F2421] bg-[#FAF8F5]'
                  : 'border-transparent text-[#736F68] hover:text-[#1F2421]'
              }`}
            >
              <Icon size={14} className={isActive ? 'text-[#9E7D3B]' : 'text-[#8C877D]'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 Cols): Wedding Specs */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
                <Sparkles size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Palace Wedding Specifications</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Palace Venue & Destination
                  </span>
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                    <MapPin size={14} className="text-[#9E7D3B]" />
                    <span>{project.location}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Target Wedding Date
                  </span>
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                    <Calendar size={14} className="text-[#9E7D3B]" />
                    <span>
                      {new Date(project.weddingDate).toLocaleDateString('en-IN', {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Expected Royal Guests
                  </span>
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                    <Users size={14} className="text-[#9E7D3B]" />
                    <span>{project.guestCount} Guests</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Allocated Agency Budget
                  </span>
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                    <Banknote size={14} className="text-[#9E7D3B]" />
                    <span>₹ {Number(project.estimatedBudget).toLocaleString('en-IN')}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Package Tier
                  </span>
                  <div className="inline-block px-2.5 py-1 bg-[#FAF8F5] border border-[#1F2421] font-semibold text-[#1F2421]">
                    {project.packageTier}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
                    Principal Project Manager
                  </span>
                  <div className="text-sm font-semibold text-[#1F2421]">
                    {project.projectManagerName}
                  </div>
                </div>
              </div>

              {/* Notes */}
              <div className="pt-4 border-t border-[#E5E0D8]">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block mb-1">
                  Confidential Project Directives & Notes
                </span>
                <div className="p-4 bg-[#FAF8F5] border border-[#E5E0D8] text-xs text-[#5C5850] leading-relaxed">
                  {project.notes || 'No confidential project directives recorded yet.'}
                </div>
              </div>
            </div>

            {/* Preparation Progress Bar Widget */}
            <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-serif text-lg font-semibold text-[#1F2421]">
                  Milestone Execution Progress
                </span>
                <span className="font-semibold text-[#9E7D3B]">
                  {completedMilestones} of {totalMilestones} Completed ({milestoneProgress}%)
                </span>
              </div>
              <div className="w-full bg-[#FAF8F5] border border-[#E5E0D8] h-2">
                <div 
                  className="bg-[#9E7D3B] h-full transition-all duration-300"
                  style={{ width: `${milestoneProgress}%` }}
                />
              </div>
            </div>
          </div>

          {/* Right Column: Confirmed Client Link */}
          <div className="space-y-6">
            <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
              <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
                <Heart size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Client Booking Reference</h2>
              </div>

              {project.client ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">
                      Royal Couple
                    </span>
                    <div className="text-sm font-semibold text-[#1F2421]">
                      {project.client.partner1Name} & {project.client.partner2Name}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-[#E5E0D8]/60">
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">
                      Email
                    </span>
                    <span className="font-medium text-[#1F2421]">{project.client.email}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">
                      Phone / WhatsApp
                    </span>
                    <span className="font-medium text-[#1F2421]">{project.client.phone}</span>
                  </div>

                  <div className="pt-2 border-t border-[#E5E0D8]/60">
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">
                      Registration Dossier ID
                    </span>
                    <span className="font-mono font-medium text-[#1F2421]">{project.clientId}</span>
                  </div>

                  <Link
                    to={`/clients/${project.clientId}`}
                    className="inline-flex items-center gap-1.5 text-xs text-[#9E7D3B] font-semibold hover:underline pt-2"
                  >
                    <span>View Client Dossier</span>
                    <ExternalLink size={12} />
                  </Link>
                </div>
              ) : (
                <div className="text-xs text-[#736F68]">
                  Client Reference ID: <strong className="font-mono text-[#1F2421]">{project.clientId}</strong>
                </div>
              )}
            </div>

            {/* Project Audit Meta */}
            <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-3 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-[#E5E0D8]/60">
                <span className="text-[#8C877D]">Project ID</span>
                <span className="font-mono font-semibold text-[#1F2421]">{project.projectCode}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-[#E5E0D8]/60">
                <span className="text-[#8C877D]">Setup Date</span>
                <span className="text-[#1F2421]">
                  {new Date(project.createdAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-[#8C877D]">Functions Scheduled</span>
                <span className="font-semibold text-[#1F2421]">{project.functions.length}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: WEDDING FUNCTIONS */}
      {activeTab === 'functions' && (() => {
        const totalFunctionsCost = project.functions.reduce(
          (acc, fn) => acc + (Number(fn.estimatedCost) || 0),
          0
        );

        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
              <div>
                <h2 className="font-serif text-2xl text-[#1F2421]">Palace Wedding Functions</h2>
                <p className="text-xs text-[#736F68] mt-0.5">
                  Multi-day ceremony logistics (Mehendi, Haldi, Royal Sangeet, Pheras, Reception) with automated cost estimation.
                </p>
              </div>
              <button
                onClick={() => {
                  setEditingFunction(null);
                  setIsAddFunctionOpen(true);
                }}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
              >
                <Plus size={14} className="text-[#D9C496]" />
                <span>Add Function</span>
              </button>
            </div>

            {/* COST ESTIMATION SUMMARY BAR */}
            <div className="bg-[#FAF8F5] border border-[#E5E0D8] p-5 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#1F2421] text-[#D9C496] flex items-center justify-center border border-[#9E7D3B]/40">
                  <IndianRupee size={22} />
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block">
                    Total Estimated Add-On Functions Cost
                  </span>
                  <span className="font-serif text-2xl font-bold text-[#1F2421]">
                    ₹{totalFunctionsCost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-6 text-xs text-[#736F68] border-l border-[#E5E0D8] pl-6">
                <div>
                  <span className="block text-[10px] uppercase tracking-wider text-[#8C877D]">Total Ceremonies</span>
                  <span className="font-semibold text-[#1F2421] text-sm">{project.functions.length} functions</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase tracking-wider text-[#8C877D]">Avg Cost / Function</span>
                  <span className="font-semibold text-[#1F2421] text-sm">
                    ₹{project.functions.length > 0
                      ? Math.round(totalFunctionsCost / project.functions.length).toLocaleString('en-IN')
                      : '0'}
                  </span>
                </div>
              </div>
            </div>

            {project.functions.length === 0 ? (
              <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center max-w-md mx-auto space-y-3">
                <Calendar size={28} className="mx-auto text-[#9E7D3B]" />
                <h3 className="font-serif text-lg text-[#1F2421]">No Functions Added Yet</h3>
                <p className="text-xs text-[#736F68]">
                  Add ceremonies and function run-sheets for this palace wedding.
                </p>
                <button
                  onClick={() => {
                    setEditingFunction(null);
                    setIsAddFunctionOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold"
                >
                  <Plus size={14} className="text-[#D9C496]" />
                  <span>Add First Function</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {project.functions.map((fn) => (
                  <div key={fn.id} className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold border bg-[#FAF8F5] border-[#E5E0D8] text-[#1F2421]">
                          {fn.status}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-[10px] font-semibold bg-[#FAF8F5] border border-[#D9C496] text-[#9E7D3B]">
                          <IndianRupee size={11} />
                          <span>Estimated Cost: ₹{Number(fn.estimatedCost || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setEditingFunction(fn);
                            setIsAddFunctionOpen(true);
                          }}
                          className="p-1.5 text-[#736F68] hover:text-[#1F2421] border border-[#E5E0D8] hover:bg-[#FAF8F5]"
                          title="Edit Function"
                        >
                          <Edit3 size={13} />
                        </button>
                        <button
                          onClick={() => handleDeleteFunction(fn.id)}
                          className="p-1.5 text-[#736F68] hover:text-[#9B2C2C] border border-[#E5E0D8] hover:bg-[#FAF8F5]"
                          title="Delete Function"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-serif text-xl font-semibold text-[#1F2421]">
                        {fn.functionName}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-[#9E7D3B] font-medium mt-1">
                        <Calendar size={13} />
                        <span>
                          {new Date(fn.functionDate).toLocaleDateString('en-IN', {
                            weekday: 'short',
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric'
                          })}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs text-[#5C5850] py-3 border-y border-[#E5E0D8]/60">
                      {(fn.startTime || fn.endTime) && (
                        <div className="flex items-center gap-2">
                          <Clock size={13} className="text-[#9E7D3B]" />
                          <span>
                            {fn.startTime || 'TBD'} — {fn.endTime || 'Late'}
                          </span>
                        </div>
                      )}

                      {fn.venue && (
                        <div className="flex items-center gap-2">
                          <MapPin size={13} className="text-[#9E7D3B]" />
                          <span>{fn.venue}</span>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[#8C877D] uppercase tracking-wider text-[10px]">Estimated Function Budget</span>
                        <span className="font-semibold text-[#9E7D3B]">
                          ₹{Number(fn.estimatedCost || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                    </div>

                    {fn.description && (
                      <p className="text-xs text-[#736F68] bg-[#FAF8F5] p-3 border border-[#E5E0D8] leading-relaxed">
                        {fn.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })()}

      {/* TAB 3: MILESTONES & TIMELINE */}
      {activeTab === 'milestones' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
            <div>
              <h2 className="font-serif text-2xl text-[#1F2421]">Project Milestones & Deadlines</h2>
              <p className="text-xs text-[#736F68] mt-0.5">
                High-level operational checkpoints and preparation deadlines before wedding day.
              </p>
            </div>
            <button
              onClick={() => setIsAddMilestoneOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
            >
              <Plus size={14} className="text-[#D9C496]" />
              <span>Add Milestone</span>
            </button>
          </div>

          <div className="space-y-3">
            {project.milestones.map((ms) => {
              const isCompleted = ms.status === 'Completed';
              const isOverdue = !isCompleted && new Date(ms.dueDate) < new Date();

              return (
                <div
                  key={ms.id}
                  className={`bg-[#FFFFFF] border p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                    isCompleted 
                      ? 'border-[#C3D9C9] bg-[#FAFDFB]' 
                      : isOverdue 
                        ? 'border-[#F87171] bg-[#FFFBFB]' 
                        : 'border-[#E5E0D8]'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => handleToggleMilestone(ms)}
                      className={`mt-0.5 p-1 border transition-colors ${
                        isCompleted
                          ? 'bg-[#1F2421] border-[#1F2421] text-[#FAF8F5]'
                          : 'border-[#8C877D] hover:border-[#1F2421] text-transparent'
                      }`}
                    >
                      <CheckCircle size={14} className={isCompleted ? 'block' : 'invisible'} />
                    </button>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`font-serif text-base font-semibold ${isCompleted ? 'line-through text-[#8C877D]' : 'text-[#1F2421]'}`}>
                          {ms.milestoneName}
                        </span>
                        {isOverdue && (
                          <span className="px-1.5 py-0.5 text-[9px] uppercase tracking-wider font-semibold bg-[#FEE2E2] text-[#991B1B] border border-[#FCA5A5] flex items-center gap-1">
                            <AlertTriangle size={10} />
                            <span>Overdue</span>
                          </span>
                        )}
                        {isCompleted && (
                          <span className="px-1.5 py-0.5 text-[9px] uppercase tracking-wider font-semibold bg-[#DCFCE7] text-[#166534] border border-[#86EFAC]">
                            Completed
                          </span>
                        )}
                      </div>

                      {ms.description && (
                        <p className="text-xs text-[#736F68] mt-1 leading-relaxed">
                          {ms.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-xs shrink-0 sm:self-center">
                    <div className="text-right">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Deadline</span>
                      <span className={`font-medium ${isOverdue ? 'text-[#991B1B] font-bold' : 'text-[#1F2421]'}`}>
                        {new Date(ms.dueDate).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric'
                        })}
                      </span>
                    </div>

                    <button
                      onClick={() => handleDeleteMilestone(ms.id)}
                      className="p-1.5 text-[#8C877D] hover:text-[#9B2C2C] border border-[#E5E0D8] hover:bg-[#FAF8F5]"
                      title="Remove Milestone"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: STATUS AUDIT HISTORY */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="pb-4 border-b border-[#E5E0D8]">
            <h2 className="font-serif text-2xl text-[#1F2421]">Project Status Audit Log</h2>
            <p className="text-xs text-[#736F68] mt-0.5">
              Complete chronological record of all status transitions and operational notes.
            </p>
          </div>

          <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-[1px] before:bg-[#E5E0D8]">
            {project.statusHistory.map((h) => (
              <div key={h.id} className="relative bg-[#FFFFFF] border border-[#E5E0D8] p-5 space-y-2">
                <div className="absolute -left-6 top-5 w-2.5 h-2.5 bg-[#9E7D3B] border-2 border-[#FFFFFF]" />

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[#1F2421]">
                      {h.oldStatus ? `${h.oldStatus} → ` : 'Initial: '}
                      <strong className="text-[#9E7D3B] font-bold">{h.newStatus}</strong>
                    </span>
                  </div>
                  <span className="text-[#8C877D] font-mono text-[11px]">
                    {new Date(h.changedAt).toLocaleString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>

                <div className="text-[11px] text-[#736F68]">
                  Updated by: <strong className="text-[#1F2421]">{h.changedBy}</strong>
                </div>

                {h.notes && (
                  <p className="text-xs text-[#5C5850] bg-[#FAF8F5] p-2.5 border border-[#E5E0D8] leading-relaxed">
                    "{h.notes}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: Update Project Status with Notes */}
      {isStatusModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-md p-6 space-y-4 shadow-xl">
            <h3 className="font-serif text-xl text-[#1F2421]">
              Confirm Status Transition
            </h3>
            <p className="text-xs text-[#736F68]">
              Transitioning project from <strong>{project.status}</strong> to <strong className="text-[#9E7D3B]">{targetStatus}</strong>.
            </p>

            <form onSubmit={handleConfirmStatusChange} className="space-y-4">
              <div>
                <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">
                  Transition Notes / Audit Reason (Optional)
                </label>
                <textarea
                  value={statusNotes}
                  onChange={(e) => setStatusNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                  placeholder="e.g. Venue agreements executed; commencing master vendor run-sheets."
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsStatusModalOpen(false)}
                  className="px-4 py-2 border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#736F68]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
                >
                  Confirm Transition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Add / Edit Function */}
      {isAddFunctionOpen && (
        <FunctionModal
          projectId={project.id}
          existing={editingFunction}
          onClose={() => setIsAddFunctionOpen(false)}
          onSaved={() => {
            setIsAddFunctionOpen(false);
            fetchProjectDetails();
          }}
        />
      )}

      {/* MODAL: Add Milestone */}
      {isAddMilestoneOpen && (
        <MilestoneModal
          projectId={project.id}
          weddingDate={project.weddingDate}
          onClose={() => setIsAddMilestoneOpen(false)}
          onSaved={() => {
            setIsAddMilestoneOpen(false);
            fetchProjectDetails();
          }}
        />
      )}

      {/* MODAL: Edit Project Specs */}
      {isEditProjectOpen && (
        <EditProjectModal
          project={project}
          onClose={() => setIsEditProjectOpen(false)}
          onSaved={() => {
            setIsEditProjectOpen(false);
            fetchProjectDetails();
          }}
        />
      )}
    </div>
  );
};

// =====================================================================
// Sub-modals
// =====================================================================

const FunctionModal: React.FC<{
  projectId: string;
  existing: WeddingFunction | null;
  onClose: () => void;
  onSaved: () => void;
}> = ({ projectId, existing, onClose, onSaved }) => {
  const [functionName, setFunctionName] = useState(existing?.functionName || '');
  const [functionDate, setFunctionDate] = useState(existing?.functionDate || '');
  const [startTime, setStartTime] = useState(existing?.startTime || '');
  const [endTime, setEndTime] = useState(existing?.endTime || '');
  const [venue, setVenue] = useState(existing?.venue || '');
  const [description, setDescription] = useState(existing?.description || '');
  const [status, setStatus] = useState<FunctionStatus>(existing?.status || 'Scheduled');
  const [estimatedCost, setEstimatedCost] = useState(
    existing?.estimatedCost !== undefined && existing?.estimatedCost !== null
      ? String(existing.estimatedCost)
      : ''
  );
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: Record<string, any> = {
        functionName,
        functionDate,
        startTime: startTime || undefined,
        endTime: endTime || undefined,
        venue: venue || undefined,
        description: description || undefined,
        status,
        estimatedCost: estimatedCost ? Number(estimatedCost) : undefined
      };

      if (existing) {
        await projectApi.updateFunction(projectId, existing.id, payload);
      } else {
        await projectApi.addFunction(projectId, payload);
      }
      onSaved();
    } catch (err: any) {
      alert(err.message || 'Failed to save function.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-lg p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
          <h3 className="font-serif text-xl text-[#1F2421]">
            {existing ? 'Edit Wedding Function' : 'Add Wedding Function'}
          </h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Function Name *</label>
            <input
              type="text"
              required
              value={functionName}
              onChange={(e) => setFunctionName(e.target.value)}
              placeholder="e.g. Royal Sangeet & Sufi Night"
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Date *</label>
              <input
                type="date"
                required
                value={functionDate}
                onChange={(e) => setFunctionDate(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as FunctionStatus)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              >
                <option value="Scheduled">Scheduled</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Start Time</label>
              <input
                type="text"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                placeholder="e.g. 17:00"
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">End Time</label>
              <input
                type="text"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                placeholder="e.g. 23:00"
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Venue Location</label>
            <input
              type="text"
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              placeholder="e.g. Manek Chowk Courtyard"
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold">
                Estimated Function Cost (₹)
              </label>
              <span className="text-[10px] text-[#9E7D3B]">
                {existing ? 'Organizer adjustment' : 'Auto-calculated if blank'}
              </span>
            </div>
            <div className="relative">
              <span className="absolute left-3 top-2 text-[#8C877D] font-serif">₹</span>
              <input
                type="number"
                min="0"
                step="5000"
                value={estimatedCost}
                onChange={(e) => setEstimatedCost(e.target.value)}
                placeholder="Auto-calculated from function tier if left blank"
                className="w-full pl-7 pr-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
            </div>
            <p className="text-[10px] text-[#736F68] mt-1">
              Leave blank to automatically assign a realistic tier cost (Mehendi: ₹45k–90k, Haldi: ₹40k–85k, Sangeet: ₹1.2L–2.5L, Wedding: ₹2.5L–5L, Reception: ₹1.75L–3.5L).
            </p>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Ceremony Directives</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Specific run-sheet requirements, stage specs, floral mandap details..."
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#E5E0D8]">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-[#E5E0D8] text-[#736F68]">Cancel</button>
            <button type="submit" disabled={submitting} className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] font-semibold">
              {submitting ? 'Saving...' : 'Save Function'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const MilestoneModal: React.FC<{
  projectId: string;
  weddingDate: string;
  onClose: () => void;
  onSaved: () => void;
}> = ({ projectId, weddingDate, onClose, onSaved }) => {
  const [milestoneName, setMilestoneName] = useState('');
  const [dueDate, setDueDate] = useState(weddingDate || '');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await projectApi.addMilestone(projectId, {
        milestoneName,
        dueDate,
        description: description || undefined,
        status: 'Pending'
      });
      onSaved();
    } catch (err: any) {
      alert(err.message || 'Failed to add milestone.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-md p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
          <h3 className="font-serif text-xl text-[#1F2421]">Add Project Milestone</h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Milestone Checkpoint *</label>
            <input
              type="text"
              required
              value={milestoneName}
              onChange={(e) => setMilestoneName(e.target.value)}
              placeholder="e.g. Confirm Vintage Baraat Procession Permissions"
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Deadline Date *</label>
            <input
              type="date"
              required
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Operational Details</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Review requirements, approvals needed, agency responsibilities..."
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#E5E0D8]">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-[#E5E0D8] text-[#736F68]">Cancel</button>
            <button type="submit" disabled={submitting} className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] font-semibold">
              {submitting ? 'Adding...' : 'Add Milestone'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const EditProjectModal: React.FC<{
  project: WeddingProject;
  onClose: () => void;
  onSaved: () => void;
}> = ({ project, onClose, onSaved }) => {
  const [projectName, setProjectName] = useState(project.projectName);
  const [weddingDate, setWeddingDate] = useState(project.weddingDate);
  const [location, setLocation] = useState(project.location);
  const [guestCount, setGuestCount] = useState(project.guestCount);
  const [estimatedBudget, setEstimatedBudget] = useState(String(project.estimatedBudget));
  const [packageTier, setPackageTier] = useState(project.packageTier);
  const [projectManagerName, setProjectManagerName] = useState(project.projectManagerName);
  const [notes, setNotes] = useState(project.notes || '');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await projectApi.update(project.id, {
        projectName,
        weddingDate,
        location,
        guestCount: Number(guestCount),
        estimatedBudget,
        packageTier,
        projectManagerName,
        notes: notes || undefined
      });
      onSaved();
    } catch (err: any) {
      alert(err.message || 'Failed to update project.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-lg p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
          <h3 className="font-serif text-xl text-[#1F2421]">Edit Project Specifications</h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Project Name</label>
            <input
              type="text"
              required
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Target Date</label>
              <input
                type="date"
                required
                value={weddingDate}
                onChange={(e) => setWeddingDate(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Venue Location</label>
              <input
                type="text"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Guest Count</label>
              <input
                type="number"
                value={guestCount}
                onChange={(e) => setGuestCount(Number(e.target.value))}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Budget (₹)</label>
              <input
                type="text"
                value={estimatedBudget}
                onChange={(e) => setEstimatedBudget(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Package Tier</label>
            <select
              value={packageTier}
              onChange={(e) => setPackageTier(e.target.value)}
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            >
              <option value="Full-Service">Full-Service Royal Production</option>
              <option value="Partial-Service">Partial-Service Heritage Coordination</option>
              <option value="Day-of Coordination">Day-of Venue & Concierge Coordination</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Project Manager</label>
            <input
              type="text"
              value={projectManagerName}
              onChange={(e) => setProjectManagerName(e.target.value)}
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-[#8C877D] font-semibold block mb-1">Confidential Notes</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#E5E0D8]">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-[#E5E0D8] text-[#736F68]">Cancel</button>
            <button type="submit" disabled={submitting} className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] font-semibold">
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
