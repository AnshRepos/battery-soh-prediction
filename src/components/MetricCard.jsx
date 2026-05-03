/**
 * MetricCard.jsx
 * Displays a single scalar metric with label, value, and optional trend/rank indicator.
 */

export default function MetricCard({ label, value, unit = '', sub, accent = 'cyan', highlight = false, icon, className = '' }) {
  const accentMap = {
    cyan:   'text-accent-cyan border-accent-cyan/20 bg-accent-cyan/5',
    green:  'text-accent-green border-accent-green/20 bg-accent-green/5',
    amber:  'text-accent-amber border-accent-amber/20 bg-accent-amber/5',
    rose:   'text-accent-rose border-accent-rose/20 bg-accent-rose/5',
    purple: 'text-accent-purple border-accent-purple/20 bg-accent-purple/5',
  }

  const accentText = {
    cyan: 'text-accent-cyan', green: 'text-accent-green',
    amber: 'text-accent-amber', rose: 'text-accent-rose', purple: 'text-accent-purple',
  }

  return (
    <div className={`card p-5 flex flex-col gap-3 ${highlight ? `border ${accentMap[accent]}` : ''} ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="section-title">{label}</p>
        {icon && (
          <div className={`w-7 h-7 rounded-md flex items-center justify-center ${accentMap[accent]}`}>
            <span className={accentText[accent]}>{icon}</span>
          </div>
        )}
      </div>

      {/* Value */}
      <div>
        <p className={`font-mono text-2xl font-bold tracking-tight ${highlight ? accentText[accent] : 'text-text-primary'}`}>
          {value}
          {unit && <span className="text-sm font-normal text-text-muted ml-1">{unit}</span>}
        </p>
        {sub && <p className="text-xs text-text-secondary mt-1">{sub}</p>}
      </div>
    </div>
  )
}
