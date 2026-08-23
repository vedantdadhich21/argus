import axios from 'axios'

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'
const API_BASE  = import.meta.env.VITE_API_BASE  || 'http://localhost:8000'

export const api = axios.create({
  baseURL: USE_MOCKS ? '' : API_BASE,
  timeout: 60_000,
  headers: {
    'ngrok-skip-browser-warning': 'true',
  },
})


export { USE_MOCKS }
