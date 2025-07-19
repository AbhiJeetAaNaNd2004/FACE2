import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { useAuthStore } from '../../store/authStore'
import {
  Users,
  UserCheck,
  Camera,
  Settings,
  BarChart3,
  Shield,
  LogOut,
  Home,
  Clock,
  Video,
  Database,
  Activity,
} from 'lucide-react'

const Sidebar: React.FC = () => {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const getNavigationItems = () => {
    const baseItems = [
      {
        title: 'Dashboard',
        href: getDashboardPath(),
        icon: Home,
        roles: ['employee', 'admin', 'super_admin'],
      },
    ]

    const employeeItems = [
      {
        title: 'My Attendance',
        href: '/employee/attendance',
        icon: Clock,
        roles: ['employee', 'admin', 'super_admin'],
      },
    ]

    const adminItems = [
      {
        title: 'Employee Management',
        href: '/admin/employees',
        icon: Users,
        roles: ['admin', 'super_admin'],
      },
      {
        title: 'Attendance Dashboard',
        href: '/admin/attendance',
        icon: UserCheck,
        roles: ['admin', 'super_admin'],
      },
      {
        title: 'Live Camera Feed',
        href: '/admin/camera-feed',
        icon: Video,
        roles: ['admin', 'super_admin'],
      },
    ]

    const superAdminItems = [
      {
        title: 'System Control',
        href: '/super-admin/system',
        icon: Activity,
        roles: ['super_admin'],
      },
      {
        title: 'User Management',
        href: '/super-admin/users',
        icon: Shield,
        roles: ['super_admin'],
      },
      {
        title: 'Camera Management',
        href: '/super-admin/cameras',
        icon: Camera,
        roles: ['super_admin'],
      },
      {
        title: 'System Logs',
        href: '/super-admin/logs',
        icon: Database,
        roles: ['super_admin'],
      },
    ]

    return [...baseItems, ...employeeItems, ...adminItems, ...superAdminItems]
  }

  const getDashboardPath = () => {
    switch (user?.role) {
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

  const navigationItems = getNavigationItems().filter((item) =>
    item.roles.includes(user?.role || 'employee')
  )

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900 text-white">
      {/* Logo/Header */}
      <div className="flex h-16 items-center justify-center border-b border-gray-700">
        <h1 className="text-xl font-bold">Face Recognition</h1>
      </div>

      {/* User Info */}
      <div className="border-b border-gray-700 p-4">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600">
            <span className="text-sm font-medium">
              {user?.username.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-gray-400 capitalize">
              {user?.role?.replace('_', ' ')}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.href
          
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.title}</span>
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="border-t border-gray-700 p-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white"
        >
          <LogOut className="h-5 w-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  )
}

export default Sidebar