# Battery SOH — Activation Function Dashboard

A production-grade **React + Vite** dashboard visualizing the results of the NASA Li-ion Battery SOH deep learning pipeline, comparing 9 activation functions across 50 training epochs.

## Live Features

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | KPI summary, best model hero, val-loss chart, RMSE bar chart |
| Leaderboard | `/leaderboard` | Sortable/filterable table of all 9 activations |
| Model Detail | `/model/:key` | Per-epoch loss/RMSE/MAE + gradient norms + raw data table |
| Plots Gallery | `/plots` | Lightbox viewer for all 7 matplotlib PNGs |
| About | `/about` | Dataset info, architecture, tech stack |

## Stack

- **React 18** + **Vite 5** — fast dev server + optimized builds
- **Tailwind CSS 3** — deep navy dark theme, JetBrains Mono + DM Sans fonts
- **Recharts** — interactive epoch charts + bar charts
- **React Router v6** — client-side routing
- **Axios** — included for future API integration

## Setup

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+

### Install & Run

```bash
# 1. Enter the project directory
cd battery-dashboard

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
# → Open http://localhost:5173

# 4. Production build
npm run build

# 5. Preview production build
npm run preview
```

## Project Structure

```
battery-dashboard/
├── index.html                    # HTML entry point (loads Google Fonts)
├── vite.config.js                # Vite config
├── tailwind.config.js            # Custom theme: navy palette, mono fonts
├── postcss.config.js
├── .env                          # VITE_API_BASE_URL (for future API use)
│
├── public/
│   └── favicon.svg               # Battery icon
│
└── src/
    ├── main.jsx                  # ReactDOM.createRoot
    ├── App.jsx                   # BrowserRouter + Routes
    ├── index.css                 # Tailwind directives + custom classes
    │
    ├── assets/
    │   ├── metrics.json          # Pre-computed ML results (50 epochs × 9 activations)
    │   └── plots/                # 7 matplotlib PNGs (bundled by Vite)
    │       ├── convergence_speed.png
    │       ├── gradient_norms.png
    │       ├── train_loss.png
    │       ├── train_mae.png
    │       ├── training_time.png
    │       ├── val_loss.png
    │       └── val_rmse.png
    │
    ├── services/
    │   └── metricsService.js     # Data layer: load, rank, reshape for charts
    │
    ├── hooks/
    │   └── useMetrics.js         # Memoized React hook wrapping metricsService
    │
    ├── components/
    │   ├── Layout.jsx            # Sidebar nav (desktop) + drawer (mobile)
    │   ├── PageHeader.jsx        # Consistent page title/subtitle/actions
    │   ├── MetricCard.jsx        # KPI card with label/value/accent
    │   ├── RankBadge.jsx         # Gold/silver/bronze rank circles
    │   ├── ActivationChip.jsx    # Colored pill tag per activation
    │   ├── EpochChart.jsx        # Multi-line Recharts epoch chart
    │   └── MetricBarChart.jsx    # Horizontal/vertical Recharts bar chart
    │
    └── pages/
        ├── DashboardPage.jsx     # /
        ├── LeaderboardPage.jsx   # /leaderboard
        ├── ModelDetailPage.jsx   # /model/:activationName
        ├── PlotsPage.jsx         # /plots
        └── AboutPage.jsx         # /about
```

## Key Data: metrics.json Schema

```jsonc
{
  "relu": {
    "history": {
      "loss":     [/* 50 train MSE values */],
      "val_loss": [/* 50 val MSE values */],
      "mae":      [/* 50 train MAE values */],
      "val_mae":  [/* 50 val MAE values */],
      "rmse":     [/* 50 train RMSE values */],
      "val_rmse": [/* 50 val RMSE values */]
    },
    "training_time":  6.83,        // seconds
    "gradient_norms": [/* 50 global L2 norms */],
    "convergence_epoch": 47,       // first epoch at ≤ 1.1× best val_loss
    "test_metrics": {
      "test_loss": 0.001974,
      "test_mae":  0.03269,
      "test_rmse": 0.04444
    }
  }
  // ... × 9 activations
}
```

## Assumptions

1. **No live REST API** — The Python project is an offline ML pipeline. All data comes from the bundled `metrics.json` and plot PNGs, loaded as Vite static assets.
2. **GELU wins** — Best test RMSE is `0.03783` (GELU), followed closely by PReLU and Mish.
3. **Future API** — If you wrap the pipeline in FastAPI (`POST /api/run`, `GET /api/results`), update `metricsService.js` to call `axios.get(import.meta.env.VITE_API_BASE_URL + '/api/results')` instead of importing the JSON directly.

## Customization

- **Colors**: Edit `tailwind.config.js` → `theme.extend.colors`
- **Activation colors**: Edit `ACTIVATION_META` in `src/services/metricsService.js`
- **Add new metrics**: Extend the `ProcessedModel` shape in `metricsService.js`, then add columns to `LeaderboardPage.jsx`
