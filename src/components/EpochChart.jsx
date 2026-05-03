/**
 * EpochChart.jsx
 * Renders a multi-line chart for per-epoch metrics (loss, MAE, RMSE, gradient norms).
 * Uses Recharts with a custom dark theme.
 */
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { ACTIVATION_META } from '../services/metricsService'

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const sorted = [...payload].sort((a, b) => a.value - b.value)

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 shadow-2xl text-xs min-w-[160px]">
      <p className="font-mono text-text-muted mb-2">Epoch {label}</p>
      {sorted.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-text-secondary">{ACTIVATION_META[entry.dataKey]?.label ?? entry.dataKey}</span>
          </span>
          <span className="font-mono text-text-primary">{Number(entry.value).toFixed(5)}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Custom Legend ────────────────────────────────────────────────────────────
function CustomLegend({ payload }) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1.5 justify-center mt-3">
      {payload?.map((entry) => (
        <span key={entry.dataKey} className="flex items-center gap-1.5 text-[10px] font-mono text-text-secondary">
          <span className="w-3 h-0.5 rounded-full inline-block" style={{ backgroundColor: entry.color }} />
          {ACTIVATION_META[entry.dataKey]?.label ?? entry.dataKey}
        </span>
      ))}
    </div>
  )
}

// ─── EpochChart ───────────────────────────────────────────────────────────────
export default function EpochChart({
  data,
  title,
  yLabel = '',
  logScale = false,
  visibleKeys = null, // null = all, array = subset of activation keys
}) {
  const allKeys = Object.keys(ACTIVATION_META)
  const keys = visibleKeys ?? allKeys

  return (
    <div className="card p-5">
      {title && (
        <p className="section-title mb-4">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2236" />
          <XAxis
            dataKey="epoch"
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
            label={{ value: 'Epoch', position: 'insideBottom', offset: -2, fill: '#4a5577', fontSize: 10 }}
          />
          <YAxis
            scale={logScale ? 'log' : 'auto'}
            domain={logScale ? ['auto', 'auto'] : undefined}
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
            width={55}
            tickFormatter={(v) => v < 0.001 ? v.toExponential(1) : v.toFixed(3)}
            label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: 10, fill: '#4a5577', fontSize: 10 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
          {keys.map((key) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={ACTIVATION_META[key]?.color ?? '#888'}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
