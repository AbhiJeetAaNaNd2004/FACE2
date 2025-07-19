import React, { useEffect, useState } from 'react'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/Table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/Dialog'
import { Input } from '../../components/ui/Input'
import { employeeAPI } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import { Plus, Edit, Trash2, Upload } from 'lucide-react'

const EmployeeManagement: React.FC = () => {
  const [employees, setEmployees] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showEnrollDialog, setShowEnrollDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null)
  const [enrollForm, setEnrollForm] = useState({
    employee_id: '',
    name: '',
    department: '',
    role: '',
    email: '',
    phone: '',
    date_joined: new Date().toISOString().split('T')[0],
  })
  const [faceImage, setFaceImage] = useState<File | null>(null)

  useEffect(() => {
    fetchEmployees()
  }, [])

  const fetchEmployees = async () => {
    try {
      setIsLoading(true)
      const response = await employeeAPI.getAll()
      setEmployees(response.data)
    } catch (error) {
      console.error('Failed to fetch employees:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!faceImage) {
      alert('Please select a face image')
      return
    }

    try {
      // Convert image to base64
      const reader = new FileReader()
      reader.onload = async () => {
        const base64Data = reader.result?.toString().split(',')[1]
        
        const enrollmentData = {
          employee: enrollForm,
          image_data: base64Data,
        }

        await employeeAPI.enroll(enrollmentData)
        setShowEnrollDialog(false)
        resetEnrollForm()
        fetchEmployees()
      }
      reader.readAsDataURL(faceImage)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to enroll employee')
    }
  }

  const handleEdit = (employee: any) => {
    setSelectedEmployee(employee)
    setShowEditDialog(true)
  }

  const handleDelete = async (employeeId: string) => {
    if (!confirm('Are you sure you want to delete this employee?')) return

    try {
      await employeeAPI.delete(employeeId)
      fetchEmployees()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete employee')
    }
  }

  const resetEnrollForm = () => {
    setEnrollForm({
      employee_id: '',
      name: '',
      department: '',
      role: '',
      email: '',
      phone: '',
      date_joined: new Date().toISOString().split('T')[0],
    })
    setFaceImage(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Employee Management</h1>
          <p className="mt-2 text-gray-600">
            Manage employee records and face recognition enrollment
          </p>
        </div>
        <Button onClick={() => setShowEnrollDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Enroll Employee
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Employees</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">Loading employees...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Date Joined</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((employee) => (
                  <TableRow key={employee.employee_id}>
                    <TableCell className="font-medium">
                      {employee.employee_id}
                    </TableCell>
                    <TableCell>{employee.name}</TableCell>
                    <TableCell>{employee.department}</TableCell>
                    <TableCell>{employee.role}</TableCell>
                    <TableCell>{formatDate(employee.date_joined)}</TableCell>
                    <TableCell>
                      <Badge
                        variant={employee.is_active ? 'success' : 'secondary'}
                      >
                        {employee.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(employee)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(employee.employee_id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Enroll Employee Dialog */}
      <Dialog open={showEnrollDialog} onOpenChange={setShowEnrollDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Enroll New Employee</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEnrollSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Employee ID
              </label>
              <Input
                value={enrollForm.employee_id}
                onChange={(e) =>
                  setEnrollForm({ ...enrollForm, employee_id: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <Input
                value={enrollForm.name}
                onChange={(e) =>
                  setEnrollForm({ ...enrollForm, name: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Department
              </label>
              <Input
                value={enrollForm.department}
                onChange={(e) =>
                  setEnrollForm({ ...enrollForm, department: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <Input
                value={enrollForm.role}
                onChange={(e) =>
                  setEnrollForm({ ...enrollForm, role: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <Input
                type="email"
                value={enrollForm.email}
                onChange={(e) =>
                  setEnrollForm({ ...enrollForm, email: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Face Image
              </label>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => setFaceImage(e.target.files?.[0] || null)}
                required
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowEnrollDialog(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                <Upload className="mr-2 h-4 w-4" />
                Enroll Employee
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default EmployeeManagement