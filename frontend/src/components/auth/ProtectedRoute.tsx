import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: 'employee' | 'admin' | 'super_admin'
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
}) => {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole) {
    const roleHierarchy = {
      employee: 1,
      admin: 2,
      super_admin: 3,
    }

    const userLevel = roleHierarchy[user.role]
    const requiredLevel = roleHierarchy[requiredRole]

    if (userLevel < requiredLevel) {
      // Redirect to appropriate dashboard based on user role
      const dashboardPath = user.role === 'admin' ? '/admin' : '/employee'
      return <Navigate to={dashboardPath} replace />
    }
  }

  return <>{children}</>
}

export default ProtectedRoute