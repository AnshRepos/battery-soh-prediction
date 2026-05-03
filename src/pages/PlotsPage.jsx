/**
 * PlotsPage.jsx
 * Gallery of all 7 pre-generated matplotlib charts with a lightbox viewer.
 * Images are imported as static assets so Vite handles the hashing/paths.
 */
import { useState } from 'react'

// ── Static imports so Vite bundles them correctly ──────────────────────────────
import convergenceSpeedImg from '../assets/plots/convergence_speed.png'
import gradientNormsImg    from '../assets/plots/gradient_norms.png'
import trainLossImg        from '../assets/plots/train_loss.png'
import trainMaeImg         from '../assets/plots/train_mae.png'
import trainingTimeImg     from '../assets/plots/training_time.png'
import valLossImg          from '../assets/plots/val_loss.png'
import valRmseImg          from '../assets/plots/val_rmse.png'

const PLOTS = [
  {
    id: 'val_loss',
    title: 'Validation Loss vs Epochs',
    description: 'MSE loss on the validation set across 50 training epochs for all 9 activation functions.',
    src: valLossImg,
    tag: 'Training',
  },
  {
    id: 'train_loss',
    title: 'Training Loss vs Epochs',
    description: 'MSE loss on the training set. Compare with validation loss to identify overfitting.',
    src: trainLossImg,
    tag: 'Training',
  },
  {
    id: 'train_mae',
    title: 'Training MAE vs Epochs',
    description: 'Mean Absolute Error on the training set — easier to interpret than MSE in physical units.',
    src: trainMaeImg,
    tag: 'Training',
  },
  {
    id: 'val_rmse',
    title: 'Validation RMSE — Final Comparison',
    description: 'Bar chart of final validation RMSE for each activation. Lower is better.',
    src: valRmseImg,
    tag: 'Summary',
  },
  {
    id: 'convergence_speed',
    title: 'Convergence Speed',
    description: 'Epochs required to reach 90% of best validation loss. Lower = faster learner.',
    src: convergenceSpeedImg,
    tag: 'Summary',
  },
  {
    id: 'training_time',
    title: 'Training Time Comparison',
    description: 'Wall-clock seconds to complete 50 training epochs per activation function.',
    src: trainingTimeImg,
    tag: 'Summary',
  },
  {
    id: 'gradient_norms',
    title: 'Global Gradient Norms',
    description: 'Global L2 gradient norm per epoch. Reveals vanishing or exploding gradient behaviour.',
    src: gradientNormsImg,
    tag: 'Diagnostics',
  },
]

const ALL_TAGS = ['All', ...Array.from(new Set(PLOTS.map((p) => p.tag)))]

// ─── Lightbox ─────────────────────────────────────────────────────────────────
function Lightbox({ plot, onClose, onPrev, onNext }) {
  if (!plot) return null
  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="relative max-w-5xl w-full bg-surface-1 rounded-2xl border border-surface-border overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-border">
          <div>
            <p className="font-display font-semibold text-text-primary">{plot.title}</p>
            <p className="text-xs text-text-secondary mt-0.5">{plot.description}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors ml-4"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Image */}
        <div className="p-6 bg-white/5">
          <img src={plot.src} alt={plot.title} className="w-full rounded-lg object-contain max-h-[60vh]" />
        </div>

        {/* Nav */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-surface-border">
          <button
            onClick={onPrev}
            className="btn-ghost text-xs flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
            Previous
          </button>
          <span className="text-xs font-mono text-text-muted">
            {PLOTS.findIndex((p) => p.id === plot.id) + 1} / {PLOTS.length}
          </span>
          <button
            onClick={onNext}
            className="btn-ghost text-xs flex items-center gap-1.5"
          >
            Next
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Plot card ────────────────────────────────────────────────────────────────
function PlotCard({ plot, onClick }) {
  const tagColors = {
    Training:    'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20',
    Summary:     'bg-accent-green/10 text-accent-green border-accent-green/20',
    Diagnostics: 'bg-accent-amber/10 text-accent-amber border-accent-amber/20',
  }

  return (
    <button
      onClick={() => onClick(plot)}
      className="card-hover text-left group overflow-hidden flex flex-col"
    >
      {/* Image */}
      <div className="bg-white/5 p-3 border-b border-surface-border overflow-hidden">
        <img
          src={plot.src}
          alt={plot.title}
          className="w-full h-44 object-contain rounded-lg group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />
      </div>

      {/* Info */}
      <div className="p-4 flex-1">
        <div className="flex items-start justify-between gap-2 mb-2">
          <p className="font-display text-sm font-semibold text-text-primary leading-snug">{plot.title}</p>
          <span className={`badge border shrink-0 ${tagColors[plot.tag] ?? 'bg-surface-3 text-text-muted border-surface-border'}`}>
            {plot.tag}
          </span>
        </div>
        <p className="text-xs text-text-secondary line-clamp-2">{plot.description}</p>
      </div>

      {/* Footer */}
      <div className="px-4 pb-4">
        <span className="text-[10px] font-mono text-accent-cyan flex items-center gap-1 group-hover:gap-2 transition-all">
          Click to enlarge
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
        </span>
      </div>
    </button>
  )
}

// ─── PlotsPage ────────────────────────────────────────────────────────────────
export default function PlotsPage() {
  const [activeTag,   setActiveTag]   = useState('All')
  const [lightboxPlot, setLightboxPlot] = useState(null)

  const filtered = activeTag === 'All' ? PLOTS : PLOTS.filter((p) => p.tag === activeTag)

  const lightboxIdx = PLOTS.findIndex((p) => p.id === lightboxPlot?.id)

  function openLightbox(plot) { setLightboxPlot(plot) }
  function closeLightbox()    { setLightboxPlot(null) }
  function prevPlot() {
    const idx = (lightboxIdx - 1 + PLOTS.length) % PLOTS.length
    setLightboxPlot(PLOTS[idx])
  }
  function nextPlot() {
    const idx = (lightboxIdx + 1) % PLOTS.length
    setLightboxPlot(PLOTS[idx])
  }

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <p className="section-title mb-2">Visualizations</p>
          <h1 className="font-display text-2xl lg:text-3xl font-semibold text-text-primary">
            Training Plots Gallery
          </h1>
          <p className="text-sm text-text-secondary mt-1.5">
            Pre-generated matplotlib charts from the full training run. Click any plot to expand.
          </p>
        </div>
        <p className="text-xs font-mono text-text-muted shrink-0 self-end sm:self-auto">
          {PLOTS.length} plots
        </p>
      </div>

      {/* Filter tags */}
      <div className="flex gap-2 flex-wrap mb-6">
        {ALL_TAGS.map((tag) => (
          <button
            key={tag}
            onClick={() => setActiveTag(tag)}
            className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-all ${
              activeTag === tag
                ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30'
                : 'bg-surface-2 text-text-secondary border-surface-border hover:border-accent-cyan/20 hover:text-text-primary'
            }`}
          >
            {tag}
            <span className="ml-1.5 text-[10px] opacity-60">
              {tag === 'All' ? PLOTS.length : PLOTS.filter((p) => p.tag === tag).length}
            </span>
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 stagger-children">
        {filtered.map((plot) => (
          <PlotCard key={plot.id} plot={plot} onClick={openLightbox} />
        ))}
      </div>

      {/* Lightbox */}
      <Lightbox
        plot={lightboxPlot}
        onClose={closeLightbox}
        onPrev={prevPlot}
        onNext={nextPlot}
      />
    </div>
  )
}
