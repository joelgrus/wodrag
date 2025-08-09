import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { ApiResponse } from '../types/api';
import { WorkoutWithSimilar, Workout, SearchResultModel } from '../types/workout';
import Credits from '../components/Credits/Credits';

interface WorkoutPageProps {
  isDarkMode: boolean;
}

function formatDateLabel(iso?: string | null): string {
  if (!iso) return '';
  // Treat ISO date as a plain date (no timezone). Avoid Date(iso) which parses as UTC.
  const parts = iso.split('-');
  if (parts.length !== 3) return iso;
  const [y, m, d] = parts.map((p) => Number(p));
  if (!y || !m || !d) return iso;
  const local = new Date(y, m - 1, d); // Local time, no TZ shift
  return local.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function dateToHashPath(iso?: string | null): string | null {
  if (!iso) return null;
  const [y, m, d] = iso.split('-');
  if (!y || !m || !d) return null;
  return `#/workouts/${y}/${m}/${d}`;
}

const SectionCard: React.FC<{ isDarkMode: boolean; children: React.ReactNode; className?: string }> = ({ isDarkMode, children, className }) => (
  <div className={`rounded-xl ring-1 ring-inset ${isDarkMode ? 'bg-white/5 ring-white/10' : 'bg-white ring-slate-200'} ${className ?? ''}`}>{children}</div>
);

const WorkoutPage: React.FC<WorkoutPageProps> = ({ isDarkMode }) => {
  const [data, setData] = useState<WorkoutWithSimilar | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [targetIso, setTargetIso] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function run() {
      const raw = window.location.hash ? window.location.hash.slice(1) : window.location.pathname;
      const match = raw.match(/^\/workouts\/(\d{4})\/(\d{2})\/(\d{2})$/);
      const params = match ? { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) } : null;
      if (!params) {
        setError('Invalid path');
        setLoading(false);
        return;
      }
      setTargetIso(`${params.year}-${String(params.month).padStart(2,'0')}-${String(params.day).padStart(2,'0')}`);
      setLoading(true);
      setError(null);
      const res: ApiResponse<WorkoutWithSimilar> = await apiService.getWorkoutByDate(
        params.year,
        params.month,
        params.day,
        5,
        'summary'
      );
      if (!mounted) return;
      if (res.success && res.data) {
        setData(res.data);
      } else {
        setError(res.error || 'Failed to load workout');
      }
      setLoading(false);
    }
    run();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className={`animate-pulse h-6 w-40 rounded ${isDarkMode ? 'bg-white/10' : 'bg-slate-200'}`} />
        <div className="mt-4 space-y-2">
          <div className={`h-4 rounded ${isDarkMode ? 'bg-white/10' : 'bg-slate-200'}`} />
          <div className={`h-4 rounded w-5/6 ${isDarkMode ? 'bg-white/10' : 'bg-slate-200'}`} />
          <div className={`h-4 rounded w-2/3 ${isDarkMode ? 'bg-white/10' : 'bg-slate-200'}`} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 space-y-4">
        <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-red-900/20 border border-red-800 text-red-200' : 'bg-red-50 border border-red-200 text-red-700'}`}>
          {error?.includes('404') ? 'No workout found for that date.' : `Error: ${error || 'No data'}`}
        </div>
        <div className="flex items-center gap-3">
          <label className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>
            Jump to date:
          </label>
          <input
            type="date"
            value={targetIso ?? ''}
            onChange={(e) => setTargetIso(e.target.value)}
            className={`px-3 py-2 rounded-md ring-1 ring-inset ${isDarkMode ? 'bg-white/5 text-gray-100 ring-white/10' : 'bg-white text-gray-900 ring-slate-300'}`}
          />
          <button
            onClick={() => {
              if (!targetIso) return;
              const [y, m, d] = targetIso.split('-');
              if (y && m && d) {
                window.location.hash = `#/workouts/${y}/${m}/${d}`;
              }
            }}
            className={`px-3 py-2 rounded-md ${isDarkMode ? 'bg-brand-600 hover:bg-brand-700 text-white' : 'bg-brand-600 hover:bg-brand-700 text-white'}`}
          >
            Go
          </button>
        </div>
      </div>
    );
  }

  const w: Workout = data.workout;
  const title = w.workout_name || 'Workout of the Day';
  const dateLabel = formatDateLabel(w.date || null);

  return (
    <div className="p-4 sm:p-6">
      <div className="flex items-baseline justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-xl font-semibold">{title}</h2>
          <div className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{dateLabel}</div>
          <div className="flex items-center gap-2 ml-auto">
            <input
              type="date"
              value={w.date ?? ''}
              onChange={(e) => {
                const iso = e.target.value;
                const [y, m, d] = iso.split('-');
                if (y && m && d) {
                  window.location.hash = `#/workouts/${y}/${m}/${d}`;
                }
              }}
              className={`px-2 py-1 rounded-md ring-1 ring-inset text-sm ${isDarkMode ? 'bg-white/5 text-gray-100 ring-white/10' : 'bg-white text-gray-900 ring-slate-300'}`}
            />
          </div>
        </div>
{(() => {
          // Use the stored URL if available, otherwise construct one from the date
          let crossfitUrl = w.url;
          if (!crossfitUrl && w.date) {
            // CrossFit.com URLs are typically in format: https://www.crossfit.com/workout/2005/08/18
            const [year, month, day] = w.date.split('-');
            crossfitUrl = `https://www.crossfit.com/workout/${year}/${month}/${day}`;
          }
          
          return crossfitUrl ? (
            <a href={crossfitUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-brand-600 hover:bg-brand-700 text-white">
              View on CrossFit.com
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 3h7m0 0v7m0-7L10 14"/></svg>
            </a>
          ) : null;
        })()}
      </div>

      {/* Summary / details */}
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <SectionCard isDarkMode={isDarkMode} className="lg:col-span-2 p-4">
          <div className="space-y-3">
            {w.one_sentence_summary ? (
              <p className={isDarkMode ? 'text-gray-200' : 'text-gray-800'}>{w.one_sentence_summary}</p>
            ) : null}
            {w.workout ? (
              <div>
                <div className={`text-sm uppercase tracking-wide ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Workout</div>
                <div className={`whitespace-pre-wrap leading-relaxed ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{w.workout}</div>
              </div>
            ) : null}
            {w.scaling ? (
              <div>
                <div className={`text-sm uppercase tracking-wide ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Scaling</div>
                <div className={`whitespace-pre-wrap leading-relaxed ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>{w.scaling}</div>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard isDarkMode={isDarkMode} className="p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Similar Workouts</h3>
          </div>
          <ul className="mt-3 space-y-2">
            {data.similar.map((s: SearchResultModel, idx) => {
              const sw = s.workout;
              const path = dateToHashPath(sw.date || null);
              return (
                <li key={(sw.id ?? idx) + 'sim'} className={`rounded-lg p-3 ring-1 ring-inset hover:translate-x-[1px] transition ${isDarkMode ? 'bg-white/5 ring-white/10 hover:bg-white/10' : 'bg-white ring-slate-200 hover:bg-slate-50'}`}>
                  <a href={path ?? sw.url ?? '#'} className="block">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">
                        {sw.workout_name || 'Workout'}
                      </div>
                      {typeof s.similarity_score === 'number' ? (
                        <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>{(s.similarity_score * 100).toFixed(0)}%</div>
                      ) : null}
                    </div>
                    {sw.date ? (
                      <div className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {formatDateLabel(sw.date)}
                      </div>
                    ) : null}
                    {sw.one_sentence_summary ? (
                      <div className={`mt-2 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{sw.one_sentence_summary}</div>
                    ) : null}
                  </a>
                </li>
              );
            })}
          </ul>
        </SectionCard>
      </div>
      
      {/* Credits */}
      <Credits isDarkMode={isDarkMode} className="mt-8 pb-6" />
    </div>
  );
};

export default WorkoutPage;
