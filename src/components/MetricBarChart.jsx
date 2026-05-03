/**
 * MetricBarChart.jsx
 * Horizontal bar chart comparing a scalar metric across all activation functions.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, ResponsiveContainer,
} from 'recharts'

function CustomTooltip({ active, payload, label, valueLabel }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 shadow-2xl text-xs">
      <p className="font-mono text-text-muted mb-1">{label}</p>
      <p className="font-mono text-text-primary font-semibold">
        {Number(payload[0].value).toFixed(5)}
        {valueLabel && <span className="text-text-muted ml-1 font-normal">{valueLabel}</span>}
      </p>
    </div>
  )
}

export default function MetricBarChart({ data, title, valueLabel = '', horizontal = false }) {
  if (horizontal) {
    return (
      <div className="card p-5">
        {title && <p className="section-title mb-4">{title}</p>}
        <ResponsiveContainer width="100%" height={data.length * 38 + 20}>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 0, right: 20, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1b2236" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
              tickLine={false}
              axisLine={{ stroke: '#2a3350' }}
              tickFormatter={(v) => v.toFixed(3)}
            />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fill: '#8a9abf', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickLine={false}
              axisLine={false}
              width={72}
            />
            <Tooltip content={<CustomTooltip valueLabel={valueLabel} />} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
              {data.map((entry) => (
                <Cell key={entry.key} fill={entry.color} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="card p-5">
      {title && <p className="section-title mb-4">{title}</p>}
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: -8, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2236" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#8a9abf', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#2a3350' }}
            interval={0}
            angle={-35}
            textAnchor="end"
          />
          <YAxis
            tick={{ fill: '#4a5577', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={false}
            width={52}
            tickFormatter={(v) => v.toFixed(3)}
          />
          <Tooltip content={<CustomTooltip valueLabel={valueLabel} />} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={32}>
            {data.map((entry) => (
              <Cell key={entry.key} fill={entry.color} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
