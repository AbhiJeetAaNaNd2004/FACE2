import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import SuperAdminDashboard from './pages/SuperAdminDashboard'
import AdminDashboard from './pages/AdminDashboard'
import EmployeeDashboard from './pages/EmployeeDashboard'
import EmployeeManagement from './pages/admin/EmployeeManagement'
import AttendanceDashboard from './pages/admin/AttendanceDashboard'
import CameraFeed from './pages/admin/CameraFeed'

function App() {
  const { isAuthenticated, user } = useAuthStore()

  // Initialize auth state from localStorage on app start
  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData)
        useAuthStore.getState().login(parsedUser, token)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
  }, [])

  const getDashboardRedirect = () => {
    if (!user) return '/login'
    
    switch (user.role) {
      case 'super_admin':
        return '/super-admin'
      case 'admin':
        return '/admin'
      case 'employee':
        return '/employee'
      default:
        return '/employee'
    }
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? (
                <Navigate to={getDashboardRedirect()} replace />
              ) : (
                <Login />
              )
            } 
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Default redirect */}
            <Route index element={<Navigate to={getDashboardRedirect()} replace />} />

            {/* Employee Routes */}
            <Route
              path="/employee"
              element={
                <ProtectedRoute requiredRole="employee">
                  <EmployeeDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employee/attendance"
              element={
                <ProtectedRoute requiredRole="employee">
                  <EmployeeDashboard />
                </ProtectedRoute>
              }
            />

            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/employees"
              element={
                <ProtectedRoute requiredRole="admin">
                  <EmployeeManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/attendance"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AttendanceDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/camera-feed"
              element={
                <ProtectedRoute requiredRole="admin">
                  <CameraFeed />
                </ProtectedRoute>
              }
            />

            {/* Super Admin Routes */}
            <Route
              path="/super-admin"
              element={
                <ProtectedRoute requiredRole="super_admin">
                  <SuperAdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/super-admin/system"
              element={
                <ProtectedRoute requiredRole="super_admin">
                  <SuperAdminDashboard />
                </ProtectedRoute>
              }
            />
            {/* Additional super admin routes would go here */}
          </Route>

          {/* Catch all route */}
          <Route path="*" element={<Navigate to={getDashboardRedirect()} replace />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App