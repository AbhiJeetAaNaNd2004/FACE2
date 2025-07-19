import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { systemAPI, employeeAPI, cameraAPI } from '../lib/api'
import { useSystemStore } from '../store/systemStore'
import { formatTime } from '../lib/utils'
import {
  Activity,
  Users,
  Camera,
  Play,
  Square,
  Loader2,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'

const SuperAdminDashboard: React.FC = () => {
  const { status, setStatus, setLoading, setError } = useSystemStore()
  const [stats, setStats] = useState({
    totalEmployees: 0,
    totalCameras: 0,
    activeCameras: 0,
  })
  const [isToggling, setIsToggling] = useState(false)

  useEffect(() => {
    fetchSystemStatus()
    fetchStats()
    
    // Refresh status every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      setLoading(true)
      const response = await systemAPI.getStatus()
      if (response.data.success) {
        setStatus(response.data.data)
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch system status')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const [employeesRes, camerasRes] = await Promise.all([
        employeeAPI.getAll(),
        cameraAPI.getAll(),
      ])

      const cameras = camerasRes.data.cameras || []
      setStats({
        totalEmployees: employeesRes.data.length,
        totalCameras: cameras.length,
        activeCameras: cameras.filter((c: any) => c.is_active).length,
      })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const handleSystemToggle = async () => {
    if (!status) return

    setIsToggling(true)
    try {
      if (status.is_running) {
        await systemAPI.stop()
      } else {
        await systemAPI.start()
      }
      
      // Refresh status after toggle
      setTimeout(fetchSystemStatus, 1000)
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to toggle system')
    } finally {
      setIsToggling(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Super Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Master control panel for the Face Recognition Attendance System
        </p>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {status?.is_running ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <Badge variant="success">Running</Badge>
                </>
              ) : (
                <>
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  <Badge variant="destructive">Stopped</Badge>
                </>
              )}
            </div>
            {status?.is_running && (
              <p className="text-xs text-muted-foreground mt-2">
                Uptime: {formatTime(status.uptime)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Cameras</CardTitle>
            <Camera className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.cam_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.activeCameras} of {stats.totalCameras} configured
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalEmployees}</div>
            <p className="text-xs text-muted-foreground">
              Registered employees
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Faces Detected</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.faces_detected || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Since system start
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Control */}
      <Card>
        <CardHeader>
          <CardTitle>System Control</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium">Face Recognition Pipeline</h3>
              <p className="text-sm text-gray-600">
                Start or stop the core face detection and recognition system
              </p>
            </div>
            <Button
              onClick={handleSystemToggle}
              disabled={isToggling || !status}
              variant={status?.is_running ? "destructive" : "default"}
              size="lg"
            >
              {isToggling ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : status?.is_running ? (
                <Square className="mr-2 h-4 w-4" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              {isToggling
                ? 'Processing...'
                : status?.is_running
                ? 'Stop System'
                : 'Start System'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      {status && (
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {status.attendance_count}
                </div>
                <div className="text-sm text-gray-600">Attendance Records</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(status.load * 100)}%
                </div>
                <div className="text-sm text-gray-600">System Load</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {status.faces_detected}
                </div>
                <div className="text-sm text-gray-600">Total Detections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {formatTime(status.uptime)}
                </div>
                <div className="text-sm text-gray-600">Uptime</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default SuperAdminDashboard