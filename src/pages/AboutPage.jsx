/**
 * AboutPage.jsx
 * Project background: dataset, model architecture, training setup, activation descriptions.
 */
import { Link } from 'react-router-dom'
import { ACTIVATION_META } from '../services/metricsService'
import PageHeader from '../components/PageHeader'
import ActivationChip from '../components/ActivationChip'

// ─── Activation descriptions ──────────────────────────────────────────────────
const ACTIVATION_DESC = {
  tanh:       'Classic hyperbolic tangent. Outputs in (−1, 1). Can suffer vanishing gradients in deep networks.',
  relu:       'Rectified Linear Unit. Simple, fast, widely used. Prone to "dying ReLU" on negative inputs.',
  leaky_relu: 'ReLU variant allowing small negative slope (α=0.3) to prevent dead neurons.',
  prelu:      'Parametric ReLU. The negative slope is a learned parameter, adapting during training.',
  elu:        'Exponential Linear Unit. Smooth negative region helps push mean activations closer to zero.',
  swish:      'x · σ(x). Self-gated, non-monotonic. Strong empirical performance in deep nets.',
  mish:       'x · tanh(softplus(x)). Smooth, non-monotonic. Similar to Swish but often smoother gradients.',
  gelu:       'Gaussian Error Linear Unit. Standard in transformers (BERT, GPT). Probabilistic gating interpretation.',
  sigmoid:    'Classic logistic function. Outputs in (0, 1). Severe vanishing gradient in hidden layers.',
}

// ─── InfoBlock ────────────────────────────────────────────────────────────────
function InfoBlock({ title, children }) {
  return (
    <div className="card p-6 space-y-3">
      <p className="font-display font-semibold text-text-primary text-base">{title}</p>
      {children}
    </div>
  )
}

function KV({ label, value }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 text-sm">
      <span className="text-text-muted font-mono text-xs w-36 shrink-0">{label}</span>
      <span className="text-text-secondary">{value}</span>
    </div>
  )
}

// ─── AboutPage ────────────────────────────────────────────────────────────────
export default function AboutPage() {
  return (
    <div className="animate-fade-in max-w-4xl">
      <PageHeader
        eyebrow="Project Info"
        title="About this Dashboard"
        subtitle="End-to-end deep learning pipeline for battery State-of-Health prediction with activation function analysis."
      />

      <div className="space-y-6">
        {/* Dataset */}
        <InfoBlock title="Dataset">
          <KV label="Source"         value="NASA Ames Li-ion Battery Aging Dataset" />
          <KV label="Repository"     value="fmardero/battery_aging (GitHub)" />
          <KV label="File"           value="discharge.csv (~21 MB, 600k+ rows)" />
          <KV label="Batteries"      value="B0005 · B0006 · B0007 · B0018" />
          <KV label="Target"         value="Discharge capacity (SOH proxy)" />
          <KV label="Features"       value="Cycle number, avg voltage, avg current, avg temperature" />
          <KV label="Split"          value="70% train · 15% val · 15% test (stratified)" />
          <KV label="Preprocessing"  value="Per-cycle aggregation → StandardScaler normalization" />
          <p className="text-xs text-text-muted mt-2">
            Raw time-series measurements are aggregated to cycle-level summaries:
            mean voltage, mean current, mean temperature, and maximum discharge capacity per cycle.
          </p>
        </InfoBlock>

        {/* Architecture */}
        <InfoBlock title="Model Architecture">
          <div className="flex flex-col gap-2">
            {[
              { layer: 'Input',    shape: '(4,)',      note: 'cycle_num, v, i, T' },
              { layer: 'Dense',    shape: '(128,)',    note: '+ Activation' },
              { layer: 'Dense',    shape: '(64,)',     note: '+ Activation' },
              { layer: 'Dense',    shape: '(32,)',     note: '+ Activation' },
              { layer: 'Output',   shape: '(1,)',      note: 'Linear — regression' },
            ].map((row) => (
              <div key={row.layer} className="flex items-center gap-3">
                <span className="w-16 text-xs font-mono text-text-muted shrink-0">{row.layer}</span>
                <span
                  className="h-6 rounded flex items-center px-3 text-xs font-mono text-accent-cyan bg-accent-cyan/10 border border-accent-cyan/20"
                  style={{ minWidth: row.shape === '(128,)' ? '9rem' : row.shape === '(64,)' ? '7rem' : row.shape === '(32,)' ? '5rem' : '3rem' }}
                >
                  {row.shape}
                </span>
                <span className="text-xs text-text-muted">{row.note}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-text-muted font-mono space-y-1">
            <p>Optimizer: Adam (default lr=0.001)</p>
            <p>Loss: MSE · Metrics: MAE, RMSE</p>
            <p>Epochs: 50 · Batch size: 32</p>
          </div>
        </InfoBlock>

        {/* Training diagnostics */}
        <InfoBlock title="Training Diagnostics">
          <p className="text-sm text-text-secondary">
            A custom <code className="font-mono text-xs bg-surface-3 px-1 py-0.5 rounded">GradientNormCallback</code> computes
            the global L2 gradient norm at the end of each epoch using a subset of 1,000 training samples.
            This reveals vanishing or exploding gradient behaviour characteristic of each activation function.
          </p>
          <p className="text-sm text-text-secondary">
            Convergence speed is defined as the epoch at which validation loss first drops to within 10% of
            its global minimum across all 50 epochs (i.e., ≤ 1.1× best val loss).
          </p>
        </InfoBlock>

        {/* Activations */}
        <InfoBlock title="Analysed Activation Functions">
          <div className="space-y-4">
            {Object.entries(ACTIVATION_DESC).map(([key, desc]) => (
              <div key={key} className="flex gap-3">
                <ActivationChip activationKey={key} />
                <p className="text-xs text-text-secondary flex-1 pt-0.5">{desc}</p>
                <Link
                  to={`/model/${key}`}
                  className="text-[10px] font-mono text-text-muted hover:text-accent-cyan transition-colors shrink-0 self-start pt-1"
                >
                  View →
                </Link>
              </div>
            ))}
          </div>
        </InfoBlock>

        {/* Tech stack */}
        <InfoBlock title="Tech Stack">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              { name: 'Python 3.13',      role: 'Runtime' },
              { name: 'TensorFlow 2.x',   role: 'ML Framework' },
              { name: 'scikit-learn',      role: 'Preprocessing' },
              { name: 'pandas + numpy',    role: 'Data layer' },
              { name: 'matplotlib + seaborn', role: 'Plotting' },
              { name: 'React 18 + Vite',   role: 'This UI' },
              { name: 'Recharts',          role: 'Interactive charts' },
              { name: 'Tailwind CSS v3',   role: 'Styling' },
              { name: 'React Router v6',   role: 'Navigation' },
            ].map(({ name, role }) => (
              <div key={name} className="bg-surface-2 rounded-lg px-3 py-2.5 border border-surface-border">
                <p className="font-mono text-xs text-text-primary">{name}</p>
                <p className="text-[10px] text-text-muted mt-0.5">{role}</p>
              </div>
            ))}
          </div>
        </InfoBlock>

        {/* CTA */}
        <div className="flex gap-3 pt-2">
          <Link to="/" className="btn-primary">View Dashboard</Link>
          <Link to="/leaderboard" className="btn-ghost">Leaderboard</Link>
          <Link to="/plots" className="btn-ghost">Plots Gallery</Link>
        </div>
      </div>
    </div>
  )
}
