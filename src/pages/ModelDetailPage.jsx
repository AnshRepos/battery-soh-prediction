/**
 * ModelDetailPage.jsx
 * Per-activation deep-dive: epoch curves for all metrics + gradient norms + stat table.
 */
import { useMemo, useState } from 'react'
import { useParams, Link, Navigate } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { getModelByKey, getAllMetrics, ACTIVATION_META } from '../services/metricsService'
import PageHeader from '../components/PageHeader'
import MetricCard from '../components/MetricCard'
import ActivationChip from '../components/ActivationChip'
import RankBadge from '../components/RankBadge'

// ─── Single-model epoch chart ─────────────────────────────────────────────────
function SingleModelChart({ title, trainData, valData, color, yLabel, convergenceEpoch }) {
  const data = trainData.map((pt, i) => ({
    epoch: pt.epoch,
    train: pt.value,
    val:   valData[i]?.value ?? null,
  }))

  return (
    <div className="card p-5">
      <p className="section-title mb-4">{title}</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2236" />
          <XAxis
            dataKey="epoch"
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
          />
          <YAxis
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
            width={52}
            tickFormatter={(v) => v < 0.001 ? v.toExponential(1) : v.toFixed(3)}
          />
          {convergenceEpoch && (
            <ReferenceLine
              x={convergenceEpoch}
              stroke="#ffb300"
              strokeDasharray="4 2"
              strokeWidth={1}
              label={{ value: `Conv.`, position: 'top', fill: '#ffb300', fontSize: 9, fontFamily: 'JetBrains Mono' }}
            />
          )}
          <Tooltip
            contentStyle={{ background: '#141928', border: '1px solid #2a3350', borderRadius: '8px', fontSize: 11 }}
            labelStyle={{ color: '#4a5577', fontFamily: 'JetBrains Mono' }}
            itemStyle={{ fontFamily: 'JetBrains Mono', color: '#e8edf8' }}
          />
          <Line type="monotone" dataKey="train" name="Train" stroke={color} strokeWidth={1.5} dot={false} strokeDasharray="5 3" />
          <Line type="monotone" dataKey="val"   name="Val"   stroke={color} strokeWidth={2}   dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 justify-center">
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-text-secondary">
          <span className="w-4 h-px border-t border-dashed" style={{ borderColor: color }} />
          Train
        </span>
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-text-secondary">
          <span className="w-4 h-0.5 rounded-full" style={{ backgroundColor: color }} />
          Validation
        </span>
        {convergenceEpoch && (
          <span className="flex items-center gap-1.5 text-[10px] font-mono text-text-secondary">
            <span className="w-4 h-px border-t border-dashed border-accent-amber" />
            Convergence
          </span>
        )}
      </div>
    </div>
  )
}

// ─── Gradient norm chart ──────────────────────────────────────────────────────
function GradientChart({ data, color }) {
  return (
    <div className="card p-5">
      <p className="section-title mb-4">Gradient Norm — Log Scale</p>
      <p className="text-xs text-text-muted mb-3">
        Global gradient norm per epoch. Low = vanishing gradients. High = exploding. Healthy range: moderate and stable.
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2236" />
          <XAxis
            dataKey="epoch"
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
          />
          <YAxis
            scale="log"
            domain={['auto', 'auto']}
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
            width={52}
            tickFormatter={(v) => v.toExponential(0)}
          />
          <Tooltip
            contentStyle={{ background: '#141928', border: '1px solid #2a3350', borderRadius: '8px', fontSize: 11 }}
            labelStyle={{ color: '#4a5577', fontFamily: 'JetBrains Mono' }}
            itemStyle={{ fontFamily: 'JetBrains Mono', color: '#e8edf8' }}
            formatter={(v) => [v.toFixed(4), 'Grad Norm']}
          />
          <Line type="monotone" dataKey="value" name="Grad Norm" stroke={color} strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─── Epoch data table ─────────────────────────────────────────────────────────
function EpochTable({ model }) {
  const [page, setPage] = useState(0)
  const PER_PAGE = 10
  const epochs = model.trainLoss.length

  const rows = useMemo(() => {
    const start = page * PER_PAGE
    return Array.from({ length: Math.min(PER_PAGE, epochs - start) }, (_, i) => {
      const e = start + i
      return {
        epoch:   e + 1,
        tLoss:   model.trainLoss[e].value,
        vLoss:   model.valLoss[e].value,
        tMae:    model.trainMae[e].value,
        vMae:    model.valMae[e].value,
        vRmse:   model.valRmse[e].value,
        gradNorm: model.gradientNorms[e].value,
      }
    })
  }, [model, page])

  const totalPages = Math.ceil(epochs / PER_PAGE)

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
        <p className="section-title">Per-Epoch Data</p>
        <div className="flex items-center gap-2">
          <button
            disabled={page === 0}
            onClick={() => setPage(p => p - 1)}
            className="text-xs font-mono px-2 py-1 rounded border border-surface-border text-text-secondary hover:border-accent-cyan/30 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Prev
          </button>
          <span className="text-xs font-mono text-text-muted">
            {page + 1}/{totalPages}
          </span>
          <button
            disabled={page === totalPages - 1}
            onClick={() => setPage(p => p + 1)}
            className="text-xs font-mono px-2 py-1 rounded border border-surface-border text-text-secondary hover:border-accent-cyan/30 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-surface-border bg-surface-2/50">
              {['Epoch', 'Train Loss', 'Val Loss', 'Train MAE', 'Val MAE', 'Val RMSE', 'Grad Norm'].map((h) => (
                <th key={h} className="px-4 py-2.5 text-right first:text-left text-[10px] text-text-muted font-medium whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.epoch}
                className={`border-b border-surface-border/40 hover:bg-surface-2/30 ${row.epoch === model.convergenceEpoch ? 'bg-accent-amber/5' : ''}`}
              >
                <td className="px-4 py-2 text-text-secondary">
                  {row.epoch}
                  {row.epoch === model.convergenceEpoch && (
                    <span className="ml-2 text-[9px] text-accent-amber">▶ Conv</span>
                  )}
                </td>
                <td className="px-4 py-2 text-right text-text-primary">{row.tLoss.toFixed(6)}</td>
                <td className="px-4 py-2 text-right text-text-primary">{row.vLoss.toFixed(6)}</td>
                <td className="px-4 py-2 text-right text-text-secondary">{row.tMae.toFixed(5)}</td>
                <td className="px-4 py-2 text-right text-text-secondary">{row.vMae.toFixed(5)}</td>
                <td className="px-4 py-2 text-right" style={{ color: model.meta.color }}>{row.vRmse.toFixed(5)}</td>
                <td className="px-4 py-2 text-right text-text-muted">{row.gradNorm.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Comparison mini-table ────────────────────────────────────────────────────
function ComparisonRow({ model, currentKey }) {
  const isCurrent = model.key === currentKey
  return (
    <Link
      to={`/model/${model.key}`}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
        isCurrent
          ? 'bg-surface-3 border border-surface-border cursor-default pointer-events-none'
          : 'hover:bg-surface-2 border border-transparent'
      }`}
    >
      <span
        className="w-1.5 h-6 rounded-full shrink-0"
        style={{ backgroundColor: model.meta.color }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-mono text-text-primary">{model.meta.label}</p>
        <p className="text-[10px] font-mono text-text-muted">{model.meta.family}</p>
      </div>
      <div className="text-right shrink-0">
        <p className="text-xs font-mono text-text-primary">{model.testRmse.toFixed(5)}</p>
        <p className="text-[10px] font-mono text-text-muted">RMSE</p>
      </div>
    </Link>
  )
}

// ─── ModelDetailPage ──────────────────────────────────────────────────────────
export default function ModelDetailPage() {
  const { activationName } = useParams()
  const model = getModelByKey(activationName)

  if (!model) return <Navigate to="/" replace />

  const allRanked = useMemo(() => {
    const all = getAllMetrics()
    return Object.values(all).sort((a, b) => a.testRmse - b.testRmse)
  }, [])
  const rank = allRanked.findIndex((m) => m.key === activationName) + 1

  return (
    <div className="animate-fade-in">
      {/* ── Breadcrumb ── */}
      <div className="flex items-center gap-2 text-xs text-text-muted mb-5 font-mono">
        <Link to="/" className="hover:text-accent-cyan transition-colors">Dashboard</Link>
        <span>/</span>
        <Link to="/leaderboard" className="hover:text-accent-cyan transition-colors">Leaderboard</Link>
        <span>/</span>
        <span className="text-text-secondary">{model.meta.label}</span>
      </div>

      <PageHeader
        eyebrow={`Rank #${rank} of 9`}
        title={`${model.meta.label} Activation`}
        subtitle={`${model.meta.family} family · 50 training epochs · 4-layer dense network (128→64→32→1)`}
        actions={
          <div className="flex gap-2">
            {rank > 1 && (
              <Link to={`/model/${allRanked[rank - 2].key}`} className="btn-ghost text-xs">
                ← {allRanked[rank - 2].meta.label}
              </Link>
            )}
            {rank < 9 && (
              <Link to={`/model/${allRanked[rank].key}`} className="btn-ghost text-xs">
                {allRanked[rank].meta.label} →
              </Link>
            )}
          </div>
        }
      />

      {/* ── KPIs ── */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <MetricCard label="Test RMSE"      value={model.testRmse.toFixed(5)}    highlight accent="cyan" />
        <MetricCard label="Test MAE"       value={model.testMae.toFixed(5)}     />
        <MetricCard label="Test Loss"      value={model.testLoss.toFixed(6)}    />
        <MetricCard label="Conv. Epoch"    value={model.convergenceEpoch}       sub="Epoch at 90% best val loss" />
        <MetricCard label="Training Time"  value={`${model.trainingTime.toFixed(2)}s`} />
      </div>

      {/* ── Main layout: charts + sidebar ── */}
      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Loss curves */}
          <SingleModelChart
            title="Loss (MSE) — Train vs Validation"
            trainData={model.trainLoss}
            valData={model.valLoss}
            color={model.meta.color}
            yLabel="MSE"
            convergenceEpoch={model.convergenceEpoch}
          />

          {/* RMSE curves */}
          <SingleModelChart
            title="RMSE — Train vs Validation"
            trainData={model.trainRmse}
            valData={model.valRmse}
            color={model.meta.color}
            yLabel="RMSE"
          />

          {/* MAE curves */}
          <SingleModelChart
            title="MAE — Train vs Validation"
            trainData={model.trainMae}
            valData={model.valMae}
            color={model.meta.color}
            yLabel="MAE"
          />

          {/* Gradient norms */}
          <GradientChart data={model.gradientNorms} color={model.meta.color} />
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Activation tag */}
          <div className="card p-5">
            <p className="section-title mb-3">Activation Info</p>
            <ActivationChip activationKey={model.key} />
            <div className="mt-4 space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-text-muted font-mono">Family</span>
                <span className="text-text-secondary">{model.meta.family}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted font-mono">Final Val Loss</span>
                <span className="font-mono text-text-primary">{model.finalValLoss.toFixed(6)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted font-mono">Final Val RMSE</span>
                <span className="font-mono text-text-primary">{model.finalValRmse.toFixed(5)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted font-mono">Final Val MAE</span>
                <span className="font-mono text-text-primary">{model.finalValMae.toFixed(5)}</span>
              </div>
            </div>
          </div>

          {/* Gradient health */}
          <div className="card p-5">
            <p className="section-title mb-3">Gradient Health</p>
            {(() => {
              const norms = model.gradientNorms.map((g) => g.value)
              const minN = Math.min(...norms)
              const maxN = Math.max(...norms)
              const lastN = norms.at(-1)
              const trend = norms.at(-1) < norms.at(-5) ? 'Decreasing' : 'Stable'
              return (
                <div className="space-y-3 text-xs">
                  {[
                    { label: 'Min Norm', value: minN.toFixed(4) },
                    { label: 'Max Norm', value: maxN.toFixed(4) },
                    { label: 'Final Norm', value: lastN.toFixed(4) },
                    { label: 'Final Trend', value: trend },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between">
                      <span className="text-text-muted font-mono">{label}</span>
                      <span className="font-mono text-text-primary">{value}</span>
                    </div>
                  ))}
                </div>
              )
            })()}
          </div>

          {/* All models comparison */}
          <div className="card overflow-hidden">
            <div className="px-5 py-3 border-b border-surface-border">
              <p className="section-title">Compare with Others</p>
            </div>
            <div className="p-2 space-y-0.5">
              {allRanked.map((m) => (
                <ComparisonRow key={m.key} model={m} currentKey={activationName} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Per-epoch data table ── */}
      <EpochTable model={model} />
    </div>
  )
}
