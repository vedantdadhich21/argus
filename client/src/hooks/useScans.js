import { useQuery } from '@tanstack/react-query'
import { api, USE_MOCKS } from '../api/client'
import mockData from '../mocks/scanResponse.json'

const MOCK_HISTORY = Array.from({ length: 8 }, (_, i) => ({
  scan_id: `mock-${i}`,
  original_filename: ['PhotoVault.apk','BankHelper.apk','notes_app.apk','FlashLight.apk','calculator.apk','GameBooster.apk','benign_notes.apk','fake_banker.apk'][i],
  final_score: [87, 72, 5, 45, 12, 68, 3, 91][i],
  severity: ['CRITICAL','HIGH','SAFE','HIGH','LOW','HIGH','SAFE','CRITICAL'][i],
  fraud_category: ['banking_trojan','overlay_phishing','benign','spyware','benign','adware','benign','sms_otp_stealer'][i],
  created_at: new Date(Date.now() - i * 3600_000).toISOString(),
}))

const MOCK_STATS = { total_scans: 142, malicious_found: 38, avg_duration_ms: 28400, unique_hashes: 139 }

export function useScans(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['scans', page],
    queryFn: async () => {
      if (USE_MOCKS) {
        await new Promise(r => setTimeout(r, 400))
        return { scans: MOCK_HISTORY, total: MOCK_HISTORY.length }
      }
      return api.get(`/api/scans?page=${page}&limit=${limit}`).then(r => r.data)
    },
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      if (USE_MOCKS) {
        await new Promise(r => setTimeout(r, 300))
        return MOCK_STATS
      }
      return api.get('/api/stats').then(r => r.data)
    },
  })
}
