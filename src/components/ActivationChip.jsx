/**
 * ActivationChip.jsx
 * A colored pill/chip displaying an activation function name.
 */
import { ACTIVATION_META } from '../services/metricsService'

export default function ActivationChip({ activationKey, size = 'md' }) {
  const meta = ACTIVATION_META[activationKey] ?? { label: activationKey, color: '#888' }
  const sz = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-mono font-medium border ${sz}`}
      style={{
        color: meta.color,
        borderColor: `${meta.color}33`,
        backgroundColor: `${meta.color}12`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ backgroundColor: meta.color }}
      />
      {meta.label}
    </span>
  )
}
