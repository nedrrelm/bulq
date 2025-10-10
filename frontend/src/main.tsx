import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import './index.css'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary'

// Create QueryClient with optimized defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // Data stays fresh for 30 seconds
      cacheTime: 300000, // Cache kept for 5 minutes
      refetchOnWindowFocus: false, // Don't refetch on window focus (can enable in production)
      retry: 1, // Retry failed requests once
      refetchOnReconnect: true, // Refetch on network reconnection
    },
    mutations: {
      retry: 0, // Don't retry mutations automatically
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
    </QueryClientProvider>
  </ErrorBoundary>,
)
