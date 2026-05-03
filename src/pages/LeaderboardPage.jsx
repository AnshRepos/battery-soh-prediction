/**
 * LeaderboardPage.jsx
 * Full sortable table of all 9 activation functions with all key metrics.
 */
import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useMetrics } from '../hooks/useMetrics'
import { getRankedModels } from '../services/metricsService'
import PageHeader from '../components/PageHeader'
import ActivationChip from '../components/ActivationChip'
import RankBadge from '../components/RankBadge'

// ─── Column definitions ────────────────────────────────────────────────────────
const COLUMNS = [
  { key: 'rank',            label: '#',             sortKey: null,              align: 'center' },
  { key: 'activation',      label: 'Activation',    sortKey: null,              align: 'left'   },
  { key: 'family',          label: 'Family',        sortKey: null,              align: 'left'   },
  { key: 'testRmse',        label: 'Test RMSE ↓',   sortKey: 'testRmse',        align: 'right'  },
  { key: 'testMae',         label: 'Test MAE ↓',    sortKey: 'testMae',         align: 'right'  },
  { key: 'testLoss',        label: 'Test Loss ↓',   sortKey: 'testLoss',        align: 'right'  },
  { key: 'finalValRmse',    label: 'Val RMSE ↓',    sortKey: 'finalValRmse',    align: 'right'  },
  { key: 'convergenceEpoch',label: 'Conv. Epoch ↑', sortKey: 'convergenceEpoch',align: 'right'  },
  { key: 'trainingTime',    label: 'Train Time',    sortKey: 'trainingTime',    align: 'right'  },
  { key: 'actions',         label: '',              sortKey: null,              align: 'center' },
]

// ─── Sort indicator ────────────────────────────────────────────────────────────
function SortIcon({ active, asc }) {
  return (
    <span className={`ml-1 font-mono ${active ? 'text-accent-cyan' : 'text-text-muted'}`}>
      {active ? (asc ? '↑' : '↓') : '⇅'}
    </span>
  )
}

// ─── Delta badge — shows how much a metric differs from best ─────────────────
function DeltaBadge({ value, best, lowerIsBetter = true }) {
  if (value === best) {
    return <span className="badge bg-accent-green/10 text-accent-green border-accent-green/20 ml-2 text-[9px]">BEST</span>
  }
  const delta = lowerIsBetter ? ((value - best) / best) * 100 : ((best - value) / best) * 100
  return (
    <span className="ml-2 font-mono text-[9px] text-text-muted">
      +{delta.toFixed(1)}%
    </span>
  )
}

// ─── LeaderboardPage ──────────────────────────────────────────────────────────
export default function LeaderboardPage() {
  const [sortKey, setSortKey]   = useState('testRmse')
  const [sortAsc, setSortAsc]   = useState(true)
  const [filterFamily, setFilterFamily] = useState('All')

  const { all } = useMetrics()

  const families = useMemo(() => {
    const f = new Set(Object.values(all).map((m) => m.meta.family))
    return ['All', ...Array.from(f).sort()]
  }, [all])

  // Sorted + filtered rows
  const rows = useMemo(() => {
    let arr = Object.values(all)
    if (filterFamily !== 'All') arr = arr.filter((m) => m.meta.family === filterFamily)
    if (sortKey) {
      arr = arr.sort((a, b) => sortAsc ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey])
    }
    return arr
  }, [all, sortKey, sortAsc, filterFamily])

  // Best values for delta indicators
  const bestValues = useMemo(() => ({
    testRmse:         Math.min(...Object.values(all).map((m) => m.testRmse)),
    testMae:          Math.min(...Object.values(all).map((m) => m.testMae)),
    testLoss:         Math.min(...Object.values(all).map((m) => m.testLoss)),
    finalValRmse:     Math.min(...Object.values(all).map((m) => m.finalValRmse)),
    convergenceEpoch: Math.min(...Object.values(all).map((m) => m.convergenceEpoch)),
    trainingTime:     Math.min(...Object.values(all).map((m) => m.trainingTime)),
  }), [all])

  // Global ranks by testRmse
  const globalRanks = useMemo(() => {
    const sorted = getRankedModels('testRmse')
    return Object.fromEntries(sorted.map((m, i) => [m.key, i + 1]))
  }, [])

  function toggleSort(key) {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(true) }
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow="Rankings"
        title="Activation Function Leaderboard"
        subtitle="All 9 activations ranked by test RMSE. Click any column header to sort."
      />

      {/* ── Filters ── */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <p className="section-title shrink-0">Filter by Family</p>
        <div className="flex gap-2 flex-wrap">
          {families.map((f) => (
            <button
              key={f}
              onClick={() => setFilterFamily(f)}
              className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-all duration-150 ${
                filterFamily === f
                  ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30'
                  : 'bg-surface-2 text-text-secondary border-surface-border hover:border-accent-cyan/20 hover:text-text-primary'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <p className="text-xs text-text-muted ml-auto font-mono">{rows.length} / 9 models</p>
      </div>

      {/* ── Table ── */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border bg-surface-2/50">
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => col.sortKey && toggleSort(col.sortKey)}
                    className={`
                      px-4 py-3 text-xs font-mono font-medium text-text-secondary whitespace-nowrap
                      text-${col.align}
                      ${col.sortKey ? 'cursor-pointer hover:text-text-primary select-none' : ''}
                      ${sortKey === col.sortKey ? 'text-accent-cyan' : ''}
                    `}
                  >
                    {col.label}
                    {col.sortKey && <SortIcon active={sortKey === col.sortKey} asc={sortAsc} />}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((model, idx) => {
                const globalRank = globalRanks[model.key]
                return (
                  <tr
                    key={model.key}
                    className="border-b border-surface-border/50 hover:bg-surface-2/40 transition-colors duration-100"
                  >
                    {/* Rank */}
                    <td className="px-4 py-3.5 text-center">
                      <RankBadge rank={globalRank} size="sm" />
                    </td>

                    {/* Activation */}
                    <td className="px-4 py-3.5">
                      <ActivationChip activationKey={model.key} />
                    </td>

                    {/* Family */}
                    <td className="px-4 py-3.5">
                      <span className="text-xs text-text-muted font-mono">{model.meta.family}</span>
                    </td>

                    {/* Test RMSE */}
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end">
                        <span className="font-mono text-xs text-text-primary">{model.testRmse.toFixed(5)}</span>
                        <DeltaBadge value={model.testRmse} best={bestValues.testRmse} />
                      </div>
                    </td>

                    {/* Test MAE */}
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end">
                        <span className="font-mono text-xs text-text-primary">{model.testMae.toFixed(5)}</span>
                        <DeltaBadge value={model.testMae} best={bestValues.testMae} />
                      </div>
                    </td>

                    {/* Test Loss */}
                    <td className="px-4 py-3.5 text-right">
                      <span className="font-mono text-xs text-text-secondary">{model.testLoss.toFixed(6)}</span>
                    </td>

                    {/* Final Val RMSE */}
                    <td className="px-4 py-3.5 text-right">
                      <span className="font-mono text-xs text-text-secondary">{model.finalValRmse.toFixed(5)}</span>
                    </td>

                    {/* Conv. Epoch */}
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${Math.max(16, (model.convergenceEpoch / 50) * 56)}px`,
                            backgroundColor: `${model.meta.color}60`,
                          }}
                        />
                        <span className="font-mono text-xs text-text-primary w-6 text-right">
                          {model.convergenceEpoch}
                        </span>
                      </div>
                    </td>

                    {/* Training Time */}
                    <td className="px-4 py-3.5 text-right">
                      <span className="font-mono text-xs text-text-secondary">{model.trainingTime.toFixed(2)}s</span>
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3.5 text-center">
                      <Link
                        to={`/model/${model.key}`}
                        className="inline-flex items-center gap-1 text-[10px] font-mono text-text-muted hover:text-accent-cyan transition-colors px-2 py-1 rounded border border-surface-border hover:border-accent-cyan/30"
                      >
                        Detail
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {rows.length === 0 && (
          <div className="text-center py-16 text-text-muted font-mono text-sm">
            No activations match the current filter.
          </div>
        )}
      </div>

      {/* ── Legend note ── */}
      <p className="text-xs text-text-muted font-mono mt-4">
        Conv. Epoch = epoch at which validation loss first reaches within 10% of its minimum (90% performance threshold).
        Lower RMSE / MAE / Loss = better. Lower convergence epoch = faster.
      </p>
    </div>
  )
}
