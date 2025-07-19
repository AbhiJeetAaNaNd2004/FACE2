import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { employeeAPI, attendanceAPI } from '../lib/api'
import { formatDate } from '../lib/utils'
import {
  Users,
  UserCheck,
  Clock,
  TrendingUp,
} from 'lucide-react'

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentEmployees: 0,
    todayAttendance: 0,
  })
  const [recentAttendance, setRecentAttendance] = useState<any[]>([])
  const [presentEmployees, setPresentEmployees] = useState<any[]>([])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [employeesRes, presentRes, attendanceRes] = await Promise.all([
        employeeAPI.getAll(),
        employeeAPI.getPresentEmployees(),
        attendanceAPI.getAll(),
      ])

      const employees = employeesRes.data
      const present = presentRes.data.present_employees
      const attendance = attendanceRes.data

      // Calculate today's attendance
      const today = new Date().toISOString().split('T')[0]
      const todayAttendance = attendance.reduce((count: number, emp: any) => {
        const todayLogs = emp.attendance_logs.filter((log: any) =>
          log.timestamp.startsWith(today)
        )
        return count + todayLogs.length
      }, 0)

      setStats({
        totalEmployees: employees.length,
        presentEmployees: present.length,
        todayAttendance,
      })

      setPresentEmployees(present)

      // Get recent attendance (last 10 records)
      const allLogs = attendance.flatMap((emp: any) =>
        emp.attendance_logs.map((log: any) => ({
          ...log,
          employee_name: emp.employee_name,
        }))
      )
      allLogs.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      setRecentAttendance(allLogs.slice(0, 10))

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Daily operational management and monitoring
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalEmployees}</div>
            <p className="text-xs text-muted-foreground">
              Registered in system
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Present Today</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.presentEmployees}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently in office
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Records</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.todayAttendance}</div>
            <p className="text-xs text-muted-foreground">
              Attendance logs today
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
              {stats.totalEmployees > 0
                ? Math.round((stats.presentEmployees / stats.totalEmployees) * 100)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              Present vs total
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Currently Present Employees */}
        <Card>
          <CardHeader>
            <CardTitle>Currently Present</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {presentEmployees.length > 0 ? (
                presentEmployees.map((employee: any) => (
                  <div
                    key={employee.employee_id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium">{employee.name}</p>
                      <p className="text-sm text-gray-600">{employee.department}</p>
                    </div>
                    <Badge variant="success">Present</Badge>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-4">
                  No employees currently present
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Attendance */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Attendance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentAttendance.length > 0 ? (
                recentAttendance.map((record: any) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium">{record.employee_name}</p>
                      <p className="text-sm text-gray-600">
                        {formatDate(record.timestamp)}
                      </p>
                    </div>
                    <Badge
                      variant={record.status === 'present' ? 'success' : 'secondary'}
                    >
                      {record.status}
                    </Badge>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-4">
                  No recent attendance records
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default AdminDashboard