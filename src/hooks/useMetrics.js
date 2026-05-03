/**
 * useMetrics.js
 * Custom hook providing memoized access to processed metrics data.
 */
import { useMemo } from 'react'
import {
  getAllMetrics,
  getRankedModels,
  getMultiLineData,
  getBarData,
  getSummaryStats,
} from '../services/metricsService'

export function useMetrics() {
  const all     = useMemo(() => getAllMetrics(), [])
  const ranked  = useMemo(() => getRankedModels('testRmse'), [])
  const summary = useMemo(() => getSummaryStats(), [])

  const getMultiLine = useMemo(() => getMultiLineData, [])
  const getBar       = useMemo(() => getBarData, [])

  return { all, ranked, summary, getMultiLine, getBar }
}
