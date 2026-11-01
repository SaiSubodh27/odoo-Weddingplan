import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Sparkles, 
  Plus, 
  Search, 
  Calendar, 
  MapPin, 
  Users, 
  Eye, 
  FolderHeart
} from 'lucide-react';
import { projectApi } from '../services/api';
import { WeddingProjectListItem, ProjectStatus } from '../types/project';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';

export const getProjectStatusStyle = (status: ProjectStatus | string) => {
  switch (status) {
    case 'Planning':
      return 'bg-[#F0F4F8] text-[#1E3A8A] border-[#BFDBFE]';
    case 'In Progress':
      return 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]';
    case 'On Hold':
      return 'bg-[#FEF3C7] text-[#B45309] border-[#FCD34D]';
    case 'Completed':
      return 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]';
    case 'Cancelled':
      return 'bg-[#F3F4F6] text-[#4B5563] border-[#E5E7EB]';
    default:
      return 'bg-[#FAF8F5] text-[#736F68] border-[#E5E0D8]';
  }
};

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<WeddingProjectListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Initial load
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await projectApi.list({
        search: search.trim() || undefined,
        status: statusFilter !== 'All' ? statusFilter : undefined
      });
      if (res && Array.isArray(res.items)) {
        setProjects(res.items);
      }
    } catch {
      // Graceful fallback to initial state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProjects();
  };

  const filteredProjects = useMemo(() => {
    return projects.filter(p => {
      const term = search.toLowerCase();
      const matchSearch = 
        !search ||
        p.projectCode.toLowerCase().includes(term) ||
        p.projectName.toLowerCase().includes(term) ||
        p.coupleName.toLowerCase().includes(term) ||
        p.location.toLowerCase().includes(term);

      const matchStatus = statusFilter === 'All' || p.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [projects, search, statusFilter]);

  // Metric stats
  const totalCount = projects.length;
  const planningCount = projects.filter(p => p.status === 'Planning').length;
  const inProgressCount = projects.filter(p => p.status === 'In Progress').length;
  const completedCount = projects.filter(p => p.status === 'Completed').length;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div>
          <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-semibold mb-1">
            <Sparkles size={13} />
            <span>Phase 3 · Production & Operations</span>
          </div>
          <h1 className="font-serif text-3xl text-[#1F2421]">Wedding Projects Management</h1>
          <p className="text-xs text-[#736F68] mt-1">
            Active royal destination projects, timelines, functions, and delivery milestones across Jaipur & Udaipur.
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors"
        >
          <Plus size={14} className="text-[#D9C496]" />
          <span>New Wedding Project</span>
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-5">
          <span className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium block">
            Total Projects
          </span>
          <div className="text-2xl font-serif font-bold text-[#1F2421] mt-1">
            {totalCount}
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-5">
          <span className="text-[10px] uppercase tracking-wider text-[#1E3A8A] font-medium block">
            In Planning
          </span>
          <div className="text-2xl font-serif font-bold text-[#1E3A8A] mt-1">
            {planningCount}
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-5">
          <span className="text-[10px] uppercase tracking-wider text-[#92400E] font-medium block">
            In Progress
          </span>
          <div className="text-2xl font-serif font-bold text-[#92400E] mt-1">
            {inProgressCount}
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-5">
          <span className="text-[10px] uppercase tracking-wider text-[#065F46] font-medium block">
            Completed
          </span>
          <div className="text-2xl font-serif font-bold text-[#065F46] mt-1">
            {completedCount}
          </div>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search size={14} className="absolute left-3 top-3 text-[#9E7D3B]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by project code (PRJ-...), couple name, palace venue..."
            className="w-full pl-9 pr-3.5 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
          />
        </form>

        {/* Status Tabs */}
        <div className="flex flex-wrap items-center gap-1">
          {(['All', 'Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 text-[11px] uppercase tracking-wider font-medium transition-colors ${
                statusFilter === st
                  ? 'bg-[#1F2421] text-[#FAF8F5]'
                  : 'bg-[#FAF8F5] text-[#736F68] hover:text-[#1F2421] border border-[#E5E0D8]'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center text-xs text-[#736F68]">
          Loading wedding projects repository...
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center max-w-lg mx-auto space-y-4">
          <div className="w-12 h-12 mx-auto bg-[#FAF8F5] border border-[#E5E0D8] flex items-center justify-center text-[#9E7D3B]">
            <FolderHeart size={24} />
          </div>
          <h3 className="font-serif text-xl text-[#1F2421]">No Wedding Projects Found</h3>
          <p className="text-xs text-[#736F68] leading-relaxed">
            {search || statusFilter !== 'All' 
              ? 'No projects match your active search filter. Try clearing the query or selecting another status.'
              : 'There are currently no wedding projects set up. Initialize a new project from any confirmed booking dossier.'}
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
          >
            <Plus size={14} className="text-[#D9C496]" />
            <span>Create Wedding Project</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((p) => {
            const milestonePercent = p.totalMilestonesCount > 0 
              ? Math.round((p.completedMilestonesCount / p.totalMilestonesCount) * 100) 
              : 0;

            const daysRemaining = Math.ceil(
              (new Date(p.weddingDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
            );

            return (
              <div
                key={p.id}
                onClick={() => navigate(`/projects/${p.id}`)}
                className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 hover:border-[#1F2421] cursor-pointer transition-all flex flex-col justify-between group"
              >
                <div>
                  {/* Top Status & Code */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className={`px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold border ${getProjectStatusStyle(p.status)}`}>
                      {p.status}
                    </span>
                    <span className="text-[11px] font-mono font-bold text-[#8C877D] tracking-wide">
                      {p.projectCode}
                    </span>
                  </div>

                  <h2 className="font-serif text-xl font-semibold text-[#1F2421] group-hover:text-[#9E7D3B] transition-colors mb-1 line-clamp-1">
                    {p.coupleName}
                  </h2>
                  <p className="text-[11px] text-[#736F68] mb-4 line-clamp-1 font-medium">
                    {p.projectName}
                  </p>

                  {/* Wedding Parameters */}
                  <div className="space-y-2.5 text-xs text-[#5C5850] py-3 border-y border-[#E5E0D8]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar size={13} className="text-[#9E7D3B] shrink-0" />
                        <span className="font-medium text-[#1F2421]">
                          {new Date(p.weddingDate).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </span>
                      </div>
                      <span className="text-[10px] uppercase font-semibold text-[#8C877D]">
                        {daysRemaining > 0 ? `${daysRemaining} days left` : 'Completed'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <MapPin size={13} className="text-[#9E7D3B] shrink-0" />
                      <span className="truncate">{p.location}</span>
                    </div>

                    <div className="flex items-center justify-between text-[11px]">
                      <span className="flex items-center gap-1.5">
                        <Users size={12} className="text-[#9E7D3B]" />
                        <span>{p.guestCount} Guests</span>
                      </span>
                      <span className="font-semibold text-[#1F2421]">
                        {p.packageTier}
                      </span>
                    </div>
                  </div>

                  {/* Functions & Milestones Summary */}
                  <div className="mt-4 space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[11px] uppercase tracking-wider text-[#8C877D] font-medium">
                        Milestone Delivery
                      </span>
                      <span className="font-semibold text-[#1F2421] text-[11px]">
                        {p.completedMilestonesCount} of {p.totalMilestonesCount} Done ({milestonePercent}%)
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-[#FAF8F5] border border-[#E5E0D8] h-1.5 overflow-hidden">
                      <div 
                        className="bg-[#9E7D3B] h-full transition-all duration-300"
                        style={{ width: `${milestonePercent}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-[11px] pt-1 text-[#736F68]">
                      <span>{p.functionsCount} Royal Functions</span>
                      <span>Manager: <strong className="text-[#1F2421]">{p.projectManagerName.split(' ')[0]}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-6 pt-4 border-t border-[#E5E0D8] flex items-center justify-between text-xs">
                  <span className="text-[#736F68]">
                    Ref: <strong className="font-mono text-[#1F2421]">{p.clientId}</strong>
                  </span>
                  <span className="flex items-center gap-1 text-[#9E7D3B] font-medium group-hover:underline">
                    <span>Manage Project</span>
                    <Eye size={12} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onProjectCreated={(newProject) => {
          fetchProjects();
          navigate(`/projects/${newProject.id}`);
        }}
      />
    </div>
  );
};
