import axios from 'axios'

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'
const API_BASE  = import.meta.env.VITE_API_BASE  || 'http://localhost:8000'

export const api = axios.create({
  baseURL: USE_MOCKS ? '' : API_BASE,
  timeout: 60_000,
})

api.interceptors.request.use((config) => {
  config.headers['ngrok-skip-browser-warning'] = '69420'
  config.headers['Accept'] = 'application/json'
  return config
})

export { USE_MOCKS }

