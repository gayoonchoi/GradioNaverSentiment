import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'
import App from './App.tsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30 * 60 * 1000, // 30분 - 이 시간 동안은 데이터를 "fresh"하다고 판단
      gcTime: 60 * 60 * 1000, // 1시간 - 컴포넌트 언마운트 후에도 1시간 동안 캐시 유지
    },
  },
})

// localStorage에 캐시를 저장하는 persister 생성
const persister = createSyncStoragePersister({
  storage: window.localStorage,
  key: 'FESTIVAL_ANALYSIS_CACHE', // localStorage 키
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <PersistQueryClientProvider
        client={queryClient}
        persistOptions={{ persister }}
      >
        <App />
      </PersistQueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
