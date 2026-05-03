/**
 * metricsService.js
 * Loads and processes the pre-computed metrics.json from the ML pipeline.
 * Since this is a static-asset project (no live REST backend), all data
 * is read from the bundled JSON file.
 */
import rawMetrics from '../assets/metrics.json'

// ─── Activation metadata ─────────────────────────────────────────────────────
export const ACTIVATION_META = {
  tanh:       { label: 'Tanh',       color: '#00e5ff', family: 'Classic' },
  relu:       { label: 'ReLU',       color: '#00ff88', family: 'Rectified' },
  leaky_relu: { label: 'Leaky ReLU', color: '#ffb300', family: 'Rectified' },
  prelu:      { label: 'PReLU',      color: '#ff8c00', family: 'Rectified' },
  elu:        { label: 'ELU',        color: '#9d7dff', family: 'Smooth' },
  swish:      { label: 'Swish',      color: '#ff4b6e', family: 'Smooth' },
  mish:       { label: 'Mish',       color: '#e040fb', family: 'Smooth' },
  gelu:       { label: 'GELU',       color: '#40c8e0', family: 'Smooth' },
  sigmoid:    { label: 'Sigmoid',    color: '#a5d6a7', family: 'Classic' },
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const round = (v, d = 5) => +v.toFixed(d)

/**
 * Returns processed data for all activations.
 * Shape: { [activationKey]: ProcessedModel }
 */
export function getAllMetrics() {
  const processed = {}

  for (const [key, data] of Object.entries(rawMetrics)) {
    const { history, training_time, gradient_norms, convergence_epoch, test_metrics } = data

    processed[key] = {
      key,
      meta: ACTIVATION_META[key] ?? { label: key, color: '#888', family: 'Other' },

      // Test set metrics (scalar)
      testRmse:  round(test_metrics.test_rmse, 5),
      testMae:   round(test_metrics.test_mae, 5),
      testLoss:  round(test_metrics.test_loss, 6),

      // Training summary
      trainingTime:     round(training_time, 2),
      convergenceEpoch: convergence_epoch,

      // Per-epoch arrays (50 epochs)
      trainLoss:    history.loss.map((v, i) => ({ epoch: i + 1, value: round(v, 6) })),
      valLoss:      history.val_loss.map((v, i) => ({ epoch: i + 1, value: round(v, 6) })),
      trainMae:     history.mae.map((v, i) => ({ epoch: i + 1, value: round(v, 5) })),
      valMae:       history.val_mae.map((v, i) => ({ epoch: i + 1, value: round(v, 5) })),
      trainRmse:    history.rmse.map((v, i) => ({ epoch: i + 1, value: round(v, 5) })),
      valRmse:      history.val_rmse.map((v, i) => ({ epoch: i + 1, value: round(v, 5) })),
      gradientNorms: gradient_norms.map((v, i) => ({ epoch: i + 1, value: round(v, 4) })),

      // Final epoch values
      finalValLoss: round(history.val_loss.at(-1), 6),
      finalValRmse: round(history.val_rmse.at(-1), 5),
      finalValMae:  round(history.val_mae.at(-1), 5),
    }
  }

  return processed
}

/**
 * Returns an array of all models sorted by a given metric (ascending).
 */
export function getRankedModels(sortBy = 'testRmse') {
  const all = getAllMetrics()
  return Object.values(all).sort((a, b) => a[sortBy] - b[sortBy])
}

/**
 * Returns chart-ready data for multi-line epoch plots.
 * Output: [{ epoch: 1, tanh: 0.xx, relu: 0.xx, ... }, ...]
 */
export function getMultiLineData(metricKey) {
  const all = getAllMetrics()
  const epochs = all['tanh'][metricKey].length

  return Array.from({ length: epochs }, (_, i) => {
    const point = { epoch: i + 1 }
    for (const [key, model] of Object.entries(all)) {
      point[key] = model[metricKey][i].value
    }
    return point
  })
}

/**
 * Returns bar chart data for a scalar metric.
 * Output: [{ key: 'relu', label: 'ReLU', value: 0.xx, color: '#...' }]
 */
export function getBarData(scalarMetricKey, sortAsc = true) {
  const all = getAllMetrics()
  const arr = Object.values(all).map((m) => ({
    key:   m.key,
    label: m.meta.label,
    value: m[scalarMetricKey],
    color: m.meta.color,
  }))
  return sortAsc ? arr.sort((a, b) => a.value - b.value) : arr.sort((a, b) => b.value - a.value)
}

/**
 * Returns a single activation's processed model.
 */
export function getModelByKey(key) {
  return getAllMetrics()[key] ?? null
}

/**
 * Returns summary statistics across all models.
 */
export function getSummaryStats() {
  const ranked = getRankedModels('testRmse')
  const best = ranked[0]
  const worst = ranked.at(-1)
  const avgRmse = ranked.reduce((s, m) => s + m.testRmse, 0) / ranked.length
  const avgTime = ranked.reduce((s, m) => s + m.trainingTime, 0) / ranked.length
  const fastestConv = ranked.slice().sort((a, b) => a.convergenceEpoch - b.convergenceEpoch)[0]

  return { best, worst, avgRmse: round(avgRmse, 5), avgTime: round(avgTime, 2), fastestConv }
}
