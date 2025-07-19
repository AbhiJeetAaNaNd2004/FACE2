import { create } from 'zustand'

interface SystemStatus {
  is_running: boolean
  uptime: number
  cam_count: number
  faces_detected: number
  attendance_count: number
  load: number
}

interface SystemState {
  status: SystemStatus | null
  isLoading: boolean
  error: string | null
  setStatus: (status: SystemStatus) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useSystemStore = create<SystemState>((set) => ({
  status: null,
  isLoading: false,
  error: null,
  
  setStatus: (status: SystemStatus) => set({ status, error: null }),
  
  setLoading: (isLoading: boolean) => set({ isLoading }),
  
  setError: (error: string | null) => set({ error, isLoading: false }),
  
  clearError: () => set({ error: null }),
}))