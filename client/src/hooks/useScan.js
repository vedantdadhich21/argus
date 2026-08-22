import { useQuery } from '@tanstack/react-query'
import { api, USE_MOCKS } from '../api/client'
import mockData from '../mocks/scanResponse.json'

const WORKING_STATUSES = [
  'queued', 'static_analysis', 'decompiling', 'pattern_scanning',
  'ioc_extraction', 'scoring', 'ai_analysis', 'building_report'
]

// Simulate mock pipeline progression
let mockCallCount = 0
const MOCK_STAGES = [
  { status: 'queued',           progress_hint: 'Queued for analysis (stage 1/8)' },
  { status: 'static_analysis', progress_hint: 'Parsing manifest & permissions (stage 2/8)' },
  { status: 'decompiling',     progress_hint: 'Decompiling bytecode (stage 3/8)' },
  { status: 'ai_analysis',     progress_hint: 'AI behavioral analysis (stage 7/8)' },
]

async function fetchMockScan() {
  await new Promise(r => setTimeout(r, 600)) // artificial delay
  if (mockCallCount < MOCK_STAGES.length) {
    const stage = MOCK_STAGES[mockCallCount++]
    return { ...mockData, ...stage }
  }
  mockCallCount = 0
  return mockData
}

export function useScan(scanId) {
  return useQuery({
    queryKey: ['scan', scanId],
    queryFn: () =>
      USE_MOCKS
        ? fetchMockScan()
        : api.get(`/api/scan/${scanId}`).then(r => r.data),
    refetchInterval: (query) =>
      WORKING_STATUSES.includes(query.state.data?.status) ? 2000 : false,
    enabled: !!scanId,
  })
}
