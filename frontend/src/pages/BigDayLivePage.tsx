import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  MapPin,
  User,
  ArrowLeft,
  Filter,
  Sparkles,
} from 'lucide-react';

interface ScheduleEvent {
  id: string;
  projectId: string;
  title: string;
  eventTime: string;
  expectedArrivalTime?: string;
  ownerName: string;
  vendorId?: string;
  vendorName?: string;
  gracePeriodMinutes: number;
  arrivedAt?: string;
  isLate: boolean;
  minutesLate: number;
  status: string;
  notes?: string;
}

interface OverviewData {
  projectId: string;
  totalEvents: number;
  arrivedCount: number;
  lateCount: number;
  pendingCount: number;
  serverTime: string;
  events: ScheduleEvent[];
}

export const BigDayLivePage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'late' | 'arrived' | 'pending'>('all');
  const [refreshing, setRefreshing] = useState(false);
  const [checkingInId, setCheckingInId] = useState<string | null>(null);

  const fetchSchedule = async (isManual = false) => {
    if (!projectId) return;
    if (isManual) setRefreshing(true);
    try {
      const res = await fetch(`/api/v1/projects/${projectId}/big-day/schedule`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err: any) {
      setError('Unable to load live Big Day schedule. Please verify connection.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
    // 30-second live polling as required in brief
    const interval = setInterval(() => {
      fetchSchedule();
    }, 30000);
    return () => clearInterval(interval);
  }, [projectId]);

  const handleCheckIn = async (eventId: string) => {
    if (!projectId) return;
    setCheckingInId(eventId);
    try {
      const res = await fetch(
        `/api/v1/projects/${projectId}/big-day/events/${eventId}/check-in`,
        { method: 'POST' }
      );
      if (res.ok) {
        await fetchSchedule();
      }
    } catch (err) {
      console.error('Check-in failed:', err);
    } finally {
      setCheckingInId(null);
    }
  };

  const filteredEvents = (data?.events || []).filter((e) => {
    if (filter === 'late') return e.isLate;
    if (filter === 'arrived') return !!e.arrivedAt;
    if (filter === 'pending') return !e.arrivedAt && !e.isLate;
    return true;
  });

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#29221D] font-sans pb-16">
      {/* Sticky Mobile-First Coordinator Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-[#E8DFD5] px-4 py-3 sm:px-6 shadow-sm">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link
              to={`/projects/${projectId}`}
              className="p-1.5 rounded-lg border border-[#E8DFD5] text-[#7C6C60] hover:bg-[#F8F4EE]"
              aria-label="Back to project"
            >
              <ArrowLeft size={16} />
            </Link>
            <div>
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-[#9C7D5C] font-semibold">
                <Sparkles size={11} />
                <span>Live Big Day Coordinator</span>
              </div>
              <h1 className="font-serif text-lg sm:text-xl font-bold text-[#2E241E]">
                Wedding Day Command
              </h1>
            </div>
          </div>

          <button
            onClick={() => fetchSchedule(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F6EFE6] text-[#78593F] rounded-lg text-xs font-semibold hover:bg-[#EFE4D6] transition"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh (30s)</span>
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-5 space-y-5">
        {/* Metric Cards Banner */}
        {data && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
            <div className="bg-white border border-[#E8DFD5] rounded-xl p-3 text-center shadow-xs">
              <span className="text-[10px] uppercase tracking-wider text-[#8C7D70]">Total Lineup</span>
              <div className="font-serif text-2xl font-bold mt-1 text-[#2B231D]">
                {data.totalEvents}
              </div>
            </div>

            <div className="bg-white border border-[#CDE5D1] rounded-xl p-3 text-center shadow-xs">
              <span className="text-[10px] uppercase tracking-wider text-[#356E3F] font-semibold">
                Checked In
              </span>
              <div className="font-serif text-2xl font-bold mt-1 text-[#2D6637]">
                {data.arrivedCount}
              </div>
            </div>

            <div
              className={`rounded-xl p-3 text-center shadow-xs border ${
                data.lateCount > 0
                  ? 'bg-[#FDF0ED] border-[#ECC1B6] text-[#A63725]'
                  : 'bg-white border-[#E8DFD5] text-[#8C7D70]'
              }`}
            >
              <span className="text-[10px] uppercase tracking-wider font-semibold flex items-center justify-center gap-1">
                {data.lateCount > 0 && <AlertTriangle size={12} />}
                Late Alerts
              </span>
              <div className="font-serif text-2xl font-bold mt-1">
                {data.lateCount}
              </div>
            </div>

            <div className="bg-white border border-[#E8DFD5] rounded-xl p-3 text-center shadow-xs">
              <span className="text-[10px] uppercase tracking-wider text-[#8C7D70]">Pending</span>
              <div className="font-serif text-2xl font-bold mt-1 text-[#64564B]">
                {data.pendingCount}
              </div>
            </div>
          </div>
        )}

        {/* Filter Pills */}
        <div className="flex gap-2 overflow-x-auto pb-1 text-xs">
          {[
            { id: 'all', label: 'All Items' },
            { id: 'late', label: `⚠️ Late Alerts (${data?.lateCount || 0})` },
            { id: 'arrived', label: `✓ Arrived (${data?.arrivedCount || 0})` },
            { id: 'pending', label: 'Upcoming' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              className={`px-3 py-1.5 rounded-full whitespace-nowrap transition font-medium ${
                filter === tab.id
                  ? 'bg-[#3A2E26] text-white shadow-xs'
                  : 'bg-white border border-[#E8DFD5] text-[#706053] hover:bg-[#F8F4EE]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white border border-[#E8DFD5] rounded-xl p-4 animate-pulse space-y-3"
              >
                <div className="h-4 bg-[#EDE5DB] rounded w-1/3"></div>
                <div className="h-3 bg-[#F2EDE6] rounded w-2/3"></div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-[#FAF0ED] border border-[#E9C3B9] rounded-xl p-4 text-[#A13A28] text-sm flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => fetchSchedule(true)}
              className="px-3 py-1 bg-[#A13A28] text-white rounded text-xs font-semibold"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredEvents.length === 0 && (
          <div className="bg-white border border-[#E8DFD5] rounded-xl p-8 text-center space-y-2">
            <Clock size={32} className="mx-auto text-[#B7A595]" />
            <h3 className="font-serif text-base font-semibold text-[#3E342D]">
              No Schedule Events Found
            </h3>
            <p className="text-xs text-[#86786C]">
              {filter !== 'all'
                ? 'No items match the current filter selection.'
                : 'No ceremony timeline events configured yet.'}
            </p>
          </div>
        )}

        {/* Events Timeline Cards (Mobile-first large touch targets) */}
        {!loading && (
          <div className="space-y-3">
            {filteredEvents.map((e) => (
              <article
                key={e.id}
                className={`bg-white rounded-xl border p-4 sm:p-5 transition shadow-xs ${
                  e.isLate
                    ? 'border-[#E8A596] ring-1 ring-[#E8A596]/40 bg-[#FFFDFD]'
                    : e.arrivedAt
                    ? 'border-[#D1E6D5]'
                    : 'border-[#E8DFD5]'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-bold bg-[#F4ECE2] text-[#694F38] px-2 py-0.5 rounded">
                        {e.eventTime}
                      </span>
                      {e.isLate ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#FAF0ED] text-[#B73D29] border border-[#EEBAB0] rounded text-[11px] font-bold uppercase tracking-wider animate-pulse">
                          <AlertTriangle size={11} />
                          {e.minutesLate}m LATE
                        </span>
                      ) : e.arrivedAt ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#EDF6EF] text-[#2C6A36] border border-[#BFDFCA] rounded text-[11px] font-semibold">
                          <CheckCircle2 size={11} />
                          Arrived
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-[#F2EEE9] text-[#7C6E61] rounded text-[11px]">
                          Scheduled
                        </span>
                      )}
                    </div>

                    <h2 className="font-serif text-lg font-semibold text-[#2B231D] truncate">
                      {e.title}
                    </h2>

                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#7A6C60]">
                      <span className="flex items-center gap-1">
                        <User size={12} className="text-[#9C7D5C]" />
                        Lead: {e.ownerName}
                      </span>
                      {e.vendorName && (
                        <span className="font-medium text-[#463930]">
                          Vendor: {e.vendorName}
                        </span>
                      )}
                    </div>

                    {e.notes && (
                      <p className="text-xs text-[#8A7C70] bg-[#FAF7F3] p-2 rounded border border-[#EDE4D9] mt-2">
                        {e.notes}
                      </p>
                    )}
                  </div>

                  {/* One-tap Check-In Action Button */}
                  <div className="shrink-0 pt-2 sm:pt-0">
                    {e.arrivedAt ? (
                      <div className="text-xs text-[#396C3E] font-medium flex items-center gap-1.5">
                        <CheckCircle2 size={15} />
                        <span>Checked in</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleCheckIn(e.id)}
                        disabled={checkingInId === e.id}
                        className={`w-full sm:w-auto px-5 py-2.5 rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center gap-2 ${
                          e.isLate
                            ? 'bg-[#B73D29] hover:bg-[#972F1D] text-white'
                            : 'bg-[#3A2E26] hover:bg-[#524238] text-white'
                        }`}
                      >
                        {checkingInId === e.id ? (
                          <RefreshCw size={13} className="animate-spin" />
                        ) : (
                          <CheckCircle2 size={14} />
                        )}
                        <span>Confirm Arrival</span>
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
