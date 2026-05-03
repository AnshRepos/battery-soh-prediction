/**
 * RankBadge.jsx
 * Shows a rank number with color coding: 1=gold, 2=silver, 3=bronze, rest=muted.
 */
export default function RankBadge({ rank, size = 'md' }) {
  const styles = {
    1: 'bg-accent-amber/15 text-accent-amber border-accent-amber/30',
    2: 'bg-zinc-400/15 text-zinc-300 border-zinc-400/30',
    3: 'bg-orange-700/15 text-orange-400 border-orange-700/30',
  }
  const base = styles[rank] || 'bg-surface-3 text-text-muted border-surface-border'
  const sz = size === 'sm' ? 'w-6 h-6 text-[10px]' : 'w-7 h-7 text-xs'

  return (
    <span className={`inline-flex items-center justify-center rounded-full border font-mono font-bold ${base} ${sz}`}>
      {rank}
    </span>
  )
}
