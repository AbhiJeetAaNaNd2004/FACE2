import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/Table'
import { attendanceAPI, employeeAPI } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import { Download, RefreshCw } from 'lucide-react'

const AttendanceDashboard: React.FC = () => {
  const [attendanceData, setAttendanceData] = useState<any[]>([])
  const [presentEmployees, setPresentEmployees] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    totalRecords: 0,
    presentToday: 0,
    absentToday: 0,
  })

  useEffect(() => {
    fetchAttendanceData()
    fetchPresentEmployees()
  }, [])

  const fetchAttendanceData = async () => {
    try {
      setIsLoading(true)
      const response = await attendanceAPI.getAll()
      const data = response.data

      setAttendanceData(data)

      // Calculate stats
      const today = new Date().toISOString().split('T')[0]
      let totalRecords = 0
      let presentToday = 0
      let absentToday = 0

      data.forEach((emp: any) => {
        emp.attendance_logs.forEach((log: any) => {
          totalRecords++
          if (log.timestamp.startsWith(today)) {
            if (log.status === 'present') {
              presentToday++
            } else {
              absentToday++
            }
          }
        })
      })

      setStats({ totalRecords, presentToday, absentToday })
    } catch (error) {
      console.error('Failed to fetch attendance data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchPresentEmployees = async () => {
    try {
      const response = await employeeAPI.getPresentEmployees()
      setPresentEmployees(response.data.present_employees)
    } catch (error) {
      console.error('Failed to fetch present employees:', error)
    }
  }

  const handleRefresh = () => {
    fetchAttendanceData()
    fetchPresentEmployees()
  }

  const exportAttendance = () => {
    // Simple CSV export
    const csvData = attendanceData.flatMap((emp: any) =>
      emp.attendance_logs.map((log: any) => ({
        employee_id: emp.employee_id,
        employee_name: emp.employee_name,
        timestamp: log.timestamp,
        status: log.status,
        confidence_score: log.confidence_score,
        notes: log.notes,
      }))
    )

    const csvContent = [
      'Employee ID,Employee Name,Timestamp,Status,Confidence,Notes',
      ...csvData.map((row: any) =>
        Object.values(row).map((val: any) => `"${val || ''}"`).join(',')
      ),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `attendance_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Attendance Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Monitor and manage employee attendance records
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={exportAttendance}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalRecords}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Present Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.presentToday}
            </div>
            <p className="text-xs text-muted-foreground">Marked present</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Absent Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.absentToday}
            </div>
            <p className="text-xs text-muted-foreground">Marked absent</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Currently Present */}
        <Card>
          <CardHeader>
            <CardTitle>Currently Present ({presentEmployees.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {presentEmployees.map((employee: any) => (
                <div
                  key={employee.employee_id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">{employee.name}</p>
                    <p className="text-sm text-gray-600">
                      {employee.department} • {employee.role}
                    </p>
                  </div>
                  <Badge variant="success">Present</Badge>
                </div>
              ))}
              {presentEmployees.length === 0 && (
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
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {attendanceData
                .flatMap((emp: any) =>
                  emp.attendance_logs.map((log: any) => ({
                    ...log,
                    employee_name: emp.employee_name,
                  }))
                )
                .sort((a: any, b: any) => 
                  new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
                )
                .slice(0, 10)
                .map((record: any) => (
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
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant={record.status === 'present' ? 'success' : 'secondary'}
                      >
                        {record.status}
                      </Badge>
                      {record.confidence_score && (
                        <span className="text-xs text-gray-500">
                          {Math.round(record.confidence_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* All Attendance Records */}
      <Card>
        <CardHeader>
          <CardTitle>All Attendance Records</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">Loading attendance data...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attendanceData
                  .flatMap((emp: any) =>
                    emp.attendance_logs.map((log: any) => ({
                      ...log,
                      employee_name: emp.employee_name,
                    }))
                  )
                  .sort((a: any, b: any) => 
                    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
                  )
                  .slice(0, 50)
                  .map((record: any) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">
                        {record.employee_name}
                      </TableCell>
                      <TableCell>{formatDate(record.timestamp)}</TableCell>
                      <TableCell>
                        <Badge
                          variant={record.status === 'present' ? 'success' : 'secondary'}
                        >
                          {record.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {record.confidence_score
                          ? `${Math.round(record.confidence_score * 100)}%`
                          : '-'}
                      </TableCell>
                      <TableCell>{record.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default AttendanceDashboard