import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Navbar from './components/shared/Navbar'
import Home from './pages/Home'
import ScanDetail from './pages/ScanDetail'
import History from './pages/History'
import ApiDocs from './pages/ApiDocs'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10_000 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/"          element={<Home />} />
          <Route path="/scan/:id"  element={<ScanDetail />} />
          <Route path="/history"   element={<History />} />
          <Route path="/docs"      element={<ApiDocs />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
