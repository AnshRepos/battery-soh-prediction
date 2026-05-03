/**
 * DashboardPage.jsx
 * Overview page: KPI summary cards, best model hero, convergence and RMSE charts.
 */
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useMetrics } from '../hooks/useMetrics'
import { getBarData, getMultiLineData } from '../services/metricsService'
import PageHeader from '../components/PageHeader'
import MetricCard from '../components/MetricCard'
import MetricBarChart from '../components/MetricBarChart'
import EpochChart from '../components/EpochChart'
import ActivationChip from '../components/ActivationChip'
import RankBadge from '../components/RankBadge'

// ─── Icons ────────────────────────────────────────────────────────────────────
const TrophyIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
  </svg>
)

// ─── BestModelHero ────────────────────────────────────────────────────────────
function BestModelHero({ model, rank = 1 }) {
  return (
    <Link
      to={`/model/${model.key}`}
      className="gradient-border card-hover p-6 flex flex-col sm:flex-row gap-6 items-start sm:items-center group"
    >
      {/* Left: rank + name */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-mono font-bold"
            style={{ backgroundColor: `${model.meta.color}18`, color: model.meta.color, border: `1px solid ${model.meta.color}33` }}
          >
            #1
          </div>
        </div>
        <div>
          <p className="section-title mb-1">Best Activation</p>
          <p className="font-display text-xl font-semibold text-text-primary">{model.meta.label}</p>
          <p className="text-xs text-text-secondary mt-0.5">{model.meta.family} family</p>
        </div>
      </div>

      {/* Divider */}
      <div className="hidden sm:block w-px h-12 bg-surface-border" />

      {/* Right: metrics grid */}
      <div className="grid grid-cols-3 gap-6">
        {[
          { label: 'Test RMSE', value: model.testRmse.toFixed(5) },
          { label: 'Test MAE',  value: model.testMae.toFixed(5) },
          { label: 'Conv. Epoch', value: `${model.convergenceEpoch}` },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="section-title mb-1">{label}</p>
            <p className="font-mono text-lg font-bold" style={{ color: model.meta.color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Arrow */}
      <div className="ml-auto hidden sm:flex items-center text-text-muted group-hover:text-accent-cyan transition-colors">
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
        </svg>
      </div>
    </Link>
  )
}

// ─── Quick model cards ─────────────────────────────────────────────────────────
function ModelMiniCard({ model, rank }) {
  return (
    <Link
      to={`/model/${model.key}`}
      className="card-hover p-4 flex items-center gap-3 group"
    >
      <RankBadge rank={rank} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <ActivationChip activationKey={model.key} size="sm" />
        </div>
        <p className="font-mono text-xs text-text-secondary truncate">
          RMSE <span className="text-text-primary">{model.testRmse.toFixed(5)}</span>
        </p>
      </div>
      <svg className="w-4 h-4 text-text-muted group-hover:text-accent-cyan transition-colors shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </Link>
  )
}

// ─── DashboardPage ─────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { ranked, summary } = useMetrics()

  // Chart data (memoized)
  const valLossData   = useMemo(() => getMultiLineData('valLoss'), [])
  const rmseBarData   = useMemo(() => getBarData('testRmse', true), [])
  const timeBarData   = useMemo(() => getBarData('trainingTime', true), [])

  const top3  = ranked.slice(0, 3)
  const rest  = ranked.slice(3)

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow="Overview"
        title="Battery SOH — Activation Comparison"
        subtitle="Deep learning pipeline comparing 9 activation functions on NASA Li-ion battery aging data. 50 epochs, identical architectures."
        actions={
          <Link to="/leaderboard" className="btn-primary">
            Full Leaderboard →
          </Link>
        }
      />

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6 stagger-children">
        <MetricCard
          label="Best Test RMSE"
          value={summary.best.testRmse.toFixed(5)}
          sub={`${summary.best.meta.label} activation`}
          accent="cyan"
          highlight
          icon={<TrophyIcon />}
        />
        <MetricCard
          label="Avg Test RMSE"
          value={summary.avgRmse.toFixed(5)}
          sub="Across all 9 activations"
          accent="purple"
        />
        <MetricCard
          label="Fastest Convergence"
          value={`Ep. ${summary.fastestConv.convergenceEpoch}`}
          sub={`${summary.fastestConv.meta.label} — 90% best val loss`}
          accent="green"
          highlight
        />
        <MetricCard
          label="Avg Training Time"
          value={summary.avgTime.toFixed(1)}
          unit="s"
          sub="Per activation, 50 epochs"
          accent="amber"
        />
      </div>

      {/* ── Best model hero ── */}
      <div className="mb-6">
        <BestModelHero model={summary.best} rank={1} />
      </div>

      {/* ── Top 3 + Others ── */}
      <div className="grid lg:grid-cols-3 gap-4 mb-8">
        <div className="lg:col-span-2">
          <p className="section-title mb-3">All Activations — by Test RMSE</p>
          <div className="space-y-2 stagger-children">
            {ranked.map((model, i) => (
              <ModelMiniCard key={model.key} model={model} rank={i + 1} />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <MetricBarChart
            data={timeBarData}
            title="Training Time (seconds)"
            valueLabel="s"
          />
        </div>
      </div>

      {/* ── Charts ── */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <div>
          <p className="section-title mb-3">Validation Loss — All Activations</p>
          <EpochChart
            data={valLossData}
            yLabel="MSE"
            logScale={false}
          />
        </div>
        <div>
          <p className="section-title mb-3">Test RMSE — Final Comparison</p>
          <MetricBarChart
            data={rmseBarData}
            valueLabel="RMSE"
            horizontal={true}
          />
        </div>
      </div>
    </div>
  )
}
