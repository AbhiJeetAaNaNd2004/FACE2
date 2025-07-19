import axios from 'axios'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API endpoints
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/json', credentials),
  
  getCurrentUser: () => api.get('/auth/me'),
  
  createUser: (userData: any) => api.post('/auth/users/create', userData),
  
  getUsers: () => api.get('/auth/users'),
  
  updateUserRole: (userId: number, role: string) =>
    api.patch(`/auth/users/${userId}/role`, { role }),
  
  deleteUser: (userId: number) => api.delete(`/auth/users/${userId}`),
}

export const systemAPI = {
  getStatus: () => api.get('/system/status'),
  
  start: () => api.post('/system/start'),
  
  stop: () => api.post('/system/stop'),
  
  getLiveFaces: () => api.get('/system/live-faces'),
  
  getAttendanceData: () => api.get('/system/attendance-data'),
  
  getLogs: (limit = 100) => api.get(`/system/logs?limit=${limit}`),
  
  getCameraFeed: (cameraId: number) => `${API_BASE_URL}/system/camera-feed/${cameraId}`,
}

export const employeeAPI = {
  getAll: () => api.get('/employees/'),
  
  getById: (employeeId: string) => api.get(`/employees/${employeeId}`),
  
  enroll: (enrollmentData: any) => api.post('/employees/enroll', enrollmentData),
  
  update: (employeeId: string, data: any) =>
    api.put(`/employees/${employeeId}`, data),
  
  delete: (employeeId: string) => api.delete(`/employees/${employeeId}`),
  
  getPresentEmployees: () => api.get('/employees/present/current'),
  
  uploadFaceImage: (employeeId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/employees/${employeeId}/face-image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const attendanceAPI = {
  getMy: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    return api.get(`/attendance/me?${params}`)
  },
  
  getAll: (startDate?: string, endDate?: string, employeeId?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    if (employeeId) params.append('employee_id', employeeId)
    return api.get(`/attendance/all?${params}`)
  },
  
  getByEmployee: (employeeId: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    return api.get(`/attendance/${employeeId}?${params}`)
  },
  
  mark: (attendanceData: any) => api.post('/attendance/mark', attendanceData),
  
  getDailySummary: (date: string) =>
    api.get(`/attendance/summary/daily?target_date=${date}`),
  
  delete: (logId: number) => api.delete(`/attendance/${logId}`),
  
  getLatest: (employeeId: string) =>
    api.get(`/attendance/employee/${employeeId}/latest`),
}

export const cameraAPI = {
  discover: (networkRange = '192.168.1.0/24', timeout = 10) =>
    api.post('/cameras/discover', { network_range: networkRange, timeout }),
  
  getAll: (statusFilter?: string, activeOnly = false) => {
    const params = new URLSearchParams()
    if (statusFilter) params.append('status_filter', statusFilter)
    if (activeOnly) params.append('active_only', 'true')
    return api.get(`/cameras/?${params}`)
  },
  
  getById: (cameraId: number) => api.get(`/cameras/${cameraId}`),
  
  create: (cameraData: any) => api.post('/cameras/', cameraData),
  
  update: (cameraId: number, data: any) =>
    api.put(`/cameras/${cameraId}`, data),
  
  configure: (cameraId: number, configData: any) =>
    api.post(`/cameras/${cameraId}/configure`, configData),
  
  activate: (cameraId: number, isActive: boolean) =>
    api.post(`/cameras/${cameraId}/activate`, { is_active: isActive }),
  
  delete: (cameraId: number) => api.delete(`/cameras/${cameraId}`),
  
  getStatus: (cameraId: number) => api.get(`/cameras/${cameraId}/status`),
  
  reloadConfigurations: () => api.post('/cameras/reload-configurations'),
  
  // Tripwire management
  createTripwire: (cameraId: number, tripwireData: any) =>
    api.post(`/cameras/${cameraId}/tripwires`, tripwireData),
  
  getTripwires: (cameraId: number) => api.get(`/cameras/${cameraId}/tripwires`),
  
  updateTripwire: (tripwireId: number, data: any) =>
    api.put(`/cameras/tripwires/${tripwireId}`, data),
  
  deleteTripwire: (tripwireId: number) =>
    api.delete(`/cameras/tripwires/${tripwireId}`),
}

export const embeddingAPI = {
  getAll: (employeeId?: string) => {
    const params = employeeId ? `?employee_id=${employeeId}` : ''
    return api.get(`/embeddings/${params}`)
  },
  
  getById: (embeddingId: number) => api.get(`/embeddings/${embeddingId}`),
  
  delete: (embeddingId: number) => api.delete(`/embeddings/${embeddingId}`),
  
  getByEmployee: (employeeId: string) =>
    api.get(`/embeddings/employee/${employeeId}`),
  
  deleteAllByEmployee: (employeeId: string) =>
    api.delete(`/embeddings/employee/${employeeId}/all`),
  
  getStats: () => api.get('/embeddings/stats/summary'),
}