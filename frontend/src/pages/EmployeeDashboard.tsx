import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { attendanceAPI } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { formatDate } from '../lib/utils'
import {
  Clock,
  Calendar,
  TrendingUp,
  User,
} from 'lucide-react'

const EmployeeDashboard: React.FC = () => {
  const { user } = useAuthStore()
  const [attendanceData, setAttendanceData] = useState<any>(null)
  const [currentStatus, setCurrentStatus] = useState<string>('unknown')
  const [stats, setStats] = useState({
    totalDays: 0,
    presentDays: 0,
    attendanceRate: 0,
  })

  useEffect(() => {
    if (user?.employee_id) {
      fetchAttendanceData()
      fetchCurrentStatus()
    }
  }, [user])

  const fetchAttendanceData = async () => {
    try {
      if (!user?.employee_id) return

      const response = await attendanceAPI.getMy()
      const data = response.data

      setAttendanceData(data)

      // Calculate stats
      const logs = data.attendance_logs || []
      const presentLogs = logs.filter((log: any) => log.status === 'present')
      const attendanceRate = logs.length > 0 ? (presentLogs.length / logs.length) * 100 : 0

      setStats({
        totalDays: logs.length,
        presentDays: presentLogs.length,
        attendanceRate: Math.round(attendanceRate),
      })
    } catch (error) {
      console.error('Failed to fetch attendance data:', error)
    }
  }

  const fetchCurrentStatus = async () => {
    try {
      if (!user?.employee_id) return

      const response = await attendanceAPI.getLatest(user.employee_id)
      setCurrentStatus(response.data.current_status)
    } catch (error) {
      console.error('Failed to fetch current status:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'present':
        return <Badge variant="success">Present</Badge>
      case 'absent':
        return <Badge variant="destructive">Absent</Badge>
      default:
        return <Badge variant="secondary">Unknown</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back, {user?.username}! Here's your attendance overview.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Status</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {getStatusBadge(currentStatus)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Your current attendance status
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Days</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDays}</div>
            <p className="text-xs text-muted-foreground">
              Days with attendance records
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Present Days</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.presentDays}
            </div>
            <p className="text-xs text-muted-foreground">
              Days marked present
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {stats.attendanceRate}%
            </div>
            <p className="text-xs text-muted-foreground">
              Overall attendance rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Attendance */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Attendance History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {attendanceData?.attendance_logs?.length > 0 ? (
              attendanceData.attendance_logs
                .slice(0, 10)
                .map((record: any) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium">
                        {formatDate(record.timestamp)}
                      </p>
                      {record.notes && (
                        <p className="text-sm text-gray-600">{record.notes}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(record.status)}
                      {record.confidence_score && (
                        <span className="text-xs text-gray-500">
                          {Math.round(record.confidence_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))
            ) : (
              <p className="text-center text-gray-500 py-8">
                No attendance records found
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default EmployeeDashboard