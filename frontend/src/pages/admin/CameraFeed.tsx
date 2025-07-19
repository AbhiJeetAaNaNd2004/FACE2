import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { cameraAPI, systemAPI } from '../../lib/api'
import { RefreshCw, Camera, AlertCircle } from 'lucide-react'

const CameraFeed: React.FC = () => {
  const [cameras, setCameras] = useState<any[]>([])
  const [selectedCamera, setSelectedCamera] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [systemStatus, setSystemStatus] = useState<any>(null)

  useEffect(() => {
    fetchCameras()
    fetchSystemStatus()
  }, [])

  const fetchCameras = async () => {
    try {
      setIsLoading(true)
      const response = await cameraAPI.getAll()
      const activeCameras = response.data.cameras.filter((cam: any) => cam.is_active)
      setCameras(activeCameras)
      
      if (activeCameras.length > 0 && !selectedCamera) {
        setSelectedCamera(activeCameras[0].camera_id)
      }
    } catch (error) {
      console.error('Failed to fetch cameras:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSystemStatus = async () => {
    try {
      const response = await systemAPI.getStatus()
      if (response.data.success) {
        setSystemStatus(response.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    }
  }

  const handleRefresh = () => {
    fetchCameras()
    fetchSystemStatus()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p>Loading camera feed...</p>
        </div>
      </div>
    )
  }

  if (!systemStatus?.is_running) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Camera Feed</h1>
          <p className="mt-2 text-gray-600">
            Real-time camera feed with face detection overlay
          </p>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-yellow-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Face Detection System Not Running
            </h3>
            <p className="text-gray-600 text-center mb-4">
              The face detection system must be running to view live camera feeds.
              Please start the system from the Super Admin dashboard.
            </p>
            <Button onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Check Status
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (cameras.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Camera Feed</h1>
          <p className="mt-2 text-gray-600">
            Real-time camera feed with face detection overlay
          </p>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Camera className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Active Cameras
            </h3>
            <p className="text-gray-600 text-center mb-4">
              No active cameras are configured. Please configure cameras in the
              Camera Management section.
            </p>
            <Button onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Camera Feed</h1>
          <p className="mt-2 text-gray-600">
            Real-time camera feed with face detection overlay
          </p>
        </div>
        <Button onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Camera List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Active Cameras</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {cameras.map((camera) => (
                <button
                  key={camera.camera_id}
                  onClick={() => setSelectedCamera(camera.camera_id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedCamera === camera.camera_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{camera.camera_name}</p>
                      <p className="text-sm text-gray-600">
                        {camera.location_description || 'No location'}
                      </p>
                    </div>
                    <Badge variant="success">Active</Badge>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Camera Feed */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>
              {cameras.find((c) => c.camera_id === selectedCamera)?.camera_name ||
                'Camera Feed'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedCamera ? (
              <div className="aspect-video bg-black rounded-lg overflow-hidden">
                <img
                  src={systemAPI.getCameraFeed(selectedCamera)}
                  alt="Live Camera Feed"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgdmlld0JveD0iMCAwIDY0MCA0ODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI2NDAiIGhlaWdodD0iNDgwIiBmaWxsPSIjMzMzIi8+Cjx0ZXh0IHg9IjMyMCIgeT0iMjQwIiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiPkNhbWVyYSBGZWVkIFVuYXZhaWxhYmxlPC90ZXh0Pgo8L3N2Zz4='
                  }}
                />
              </div>
            ) : (
              <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Camera className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Select a camera to view feed</p>
                </div>
              </div>
            )}

            {selectedCamera && (
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Resolution:</span>{' '}
                  {cameras.find((c) => c.camera_id === selectedCamera)?.resolution_width}x
                  {cameras.find((c) => c.camera_id === selectedCamera)?.resolution_height}
                </div>
                <div>
                  <span className="font-medium">FPS:</span>{' '}
                  {cameras.find((c) => c.camera_id === selectedCamera)?.fps}
                </div>
                <div>
                  <span className="font-medium">Type:</span>{' '}
                  {cameras.find((c) => c.camera_id === selectedCamera)?.camera_type}
                </div>
                <div>
                  <span className="font-medium">Status:</span>{' '}
                  <Badge variant="success">Live</Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default CameraFeed