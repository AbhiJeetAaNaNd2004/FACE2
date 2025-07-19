from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from .db_config import SessionLocal
from .db_models import Employee, FaceEmbedding, AttendanceLog, TrackingRecord, SystemLog, UserAccount, CameraConfig, Tripwire
import numpy as np
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import psycopg2
from io import BytesIO
import threading

class DatabaseManager:
    def __init__(self):
        self.session_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self.Session = SessionLocal  # ✅ Set session factory

    def create_employee(self, employee_id: str, employee_name: str, department: str = None, designation: str = None, email: str = None, phone: str = None) -> bool:
        session = None
        try:
            session = self.Session()
            existing_employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if existing_employee:
                return False
            employee = Employee(
                id=employee_id,
                employee_name=employee_name,
                department=department,
                designation=designation,
                email=email,
                phone=phone)
            session.add(employee)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error creating employee {employee_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        session = None
        try:
            session = self.Session()
            return session.query(Employee).filter(Employee.id == employee_id).first()
        except Exception as e:
            self.logger.error(f"Error getting employee {employee_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_all_employees(self) -> List[Employee]:
        session = None
        try:
            session = self.Session()
            return session.query(Employee).filter(Employee.is_active == True).all()
        except Exception as e:
            self.logger.error(f"Error getting all employees: {e}")
            return []
        finally:
            if session:
                session.close()

    def store_face_embedding(self, employee_id, embedding, embedding_type, quality_score, source_image_path):
        session = None
        try:
            session = self.Session()

            # Serialize embedding to bytes
            out = BytesIO()
            np.save(out, embedding.astype(np.float32))
            out.seek(0)
            binary_embedding = out.read()

            new_embedding = FaceEmbedding(
                employee_id=employee_id,
                embedding_data=binary_embedding,
                embedding_type=embedding_type,
                quality_score=float(quality_score),
                source_image_path=source_image_path,
                is_active=True
            )
            session.add(new_embedding)
            session.commit()
            print(f"[DB] Stored embedding for {employee_id}")
            return True

        except Exception as e:
            if session:
                session.rollback()
            print(f"[DB] Error storing embedding for {employee_id}: {e}")
            return False

        finally:
            if session:
                session.close()

    def get_face_embeddings(self, employee_id: str = None, embedding_type: str = None, limit: int = None) -> List[Tuple[str, np.ndarray]]:
        session = None
        try:
            session = self.Session()
            query = session.query(FaceEmbedding).filter(FaceEmbedding.is_active == True)
            if employee_id:
                query = query.filter(FaceEmbedding.employee_id == employee_id)
            if embedding_type:
                query = query.filter(FaceEmbedding.embedding_type == embedding_type)
            query = query.order_by(desc(FaceEmbedding.created_at))
            if limit:
                query = query.limit(limit)
            results = []
            for embedding_record in query.all():
                # ✅ Deserialize bytes to numpy array
                embedding_data = np.load(BytesIO(embedding_record.embedding_data))
                results.append((embedding_record.employee_id, embedding_data))
            return results
        except Exception as e:
            self.logger.error(f"Error getting face embeddings: {e}")
            return []
        finally:
            if session:
                session.close()


    def get_all_active_embeddings(self) -> Tuple[List[np.ndarray], List[str]]:
        session = None
        try:
            session = self.Session()
            embeddings = []
            labels = []

            enroll_embeddings = session.query(FaceEmbedding).filter(
                and_(FaceEmbedding.is_active == True, FaceEmbedding.embedding_type == 'enroll')
            ).all()

            for emb_record in enroll_embeddings:
                embedding_data = pickle.loads(emb_record.embedding_data)
                embeddings.append(embedding_data)
                labels.append(emb_record.employee_id)

            update_embeddings = session.query(FaceEmbedding).filter(
                and_(FaceEmbedding.is_active == True, FaceEmbedding.embedding_type == 'update')
            ).order_by(desc(FaceEmbedding.created_at)).all()

            employee_update_count = {}
            for emb_record in update_embeddings:
                emp_id = emb_record.employee_id
                if emp_id not in employee_update_count:
                    employee_update_count[emp_id] = 0
                if employee_update_count[emp_id] < 3:
                    embedding_data = pickle.loads(emb_record.embedding_data)
                    embeddings.append(embedding_data)
                    labels.append(emb_record.employee_id)
                    employee_update_count[emp_id] += 1

            return embeddings, labels
        except Exception as e:
            self.logger.error(f"Error getting all active embeddings: {e}")
            return [], []
        finally:
            if session:
                session.close()

    def log_attendance(self, employee_id: str, camera_id: int, event_type: str, confidence_score: float = 0.0, work_status: str = 'working', notes: str = None) -> bool:
        """Log attendance record for an employee"""
        session = None
        try:
            session = self.Session()
            
            # Create attendance record
            attendance_record = AttendanceLog(
                employee_id=employee_id,
                camera_id=camera_id,
                event_type=event_type,
                confidence_score=confidence_score,
                work_status=work_status,
                notes=notes
            )
            
            session.add(attendance_record)
            session.commit()
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error logging attendance for {employee_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    # Camera Management Methods
    def create_camera(self, camera_data: dict) -> Optional[CameraConfig]:
        """Create a new camera configuration"""
        session = None
        try:
            session = self.Session()
            
            # Get the next available camera_id
            max_camera_id = session.query(func.max(CameraConfig.camera_id)).scalar()
            next_camera_id = (max_camera_id + 1) if max_camera_id is not None else 1
            
            camera = CameraConfig(
                camera_id=next_camera_id,
                camera_name=camera_data['camera_name'],
                camera_type=camera_data.get('camera_type', 'general'),
                ip_address=camera_data.get('ip_address'),
                stream_url=camera_data.get('stream_url'),
                username=camera_data.get('username'),
                password=camera_data.get('password'),
                resolution_width=camera_data.get('resolution_width', 1920),
                resolution_height=camera_data.get('resolution_height', 1080),
                fps=camera_data.get('fps', 30),
                gpu_id=camera_data.get('gpu_id', 0),
                status=camera_data.get('status', 'discovered'),
                is_active=camera_data.get('is_active', False),
                location_description=camera_data.get('location_description'),
                manufacturer=camera_data.get('manufacturer'),
                model=camera_data.get('model'),
                firmware_version=camera_data.get('firmware_version'),
                onvif_supported=camera_data.get('onvif_supported', False)
            )
            
            session.add(camera)
            session.commit()
            session.refresh(camera)
            
            self.logger.info(f"Created camera {camera.camera_id}: {camera.camera_name}")
            return camera
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error creating camera: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_camera(self, camera_id: int) -> Optional[CameraConfig]:
        """Get camera configuration by ID"""
        session = None
        try:
            session = self.Session()
            return session.query(CameraConfig).filter(CameraConfig.camera_id == camera_id).first()
        except Exception as e:
            self.logger.error(f"Error getting camera {camera_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_all_cameras(self) -> List[CameraConfig]:
        """Get all camera configurations"""
        session = None
        try:
            session = self.Session()
            return session.query(CameraConfig).all()
        except Exception as e:
            self.logger.error(f"Error getting all cameras: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_active_cameras(self) -> List[CameraConfig]:
        """Get all active camera configurations"""
        session = None
        try:
            session = self.Session()
            return session.query(CameraConfig).filter(CameraConfig.is_active == True).all()
        except Exception as e:
            self.logger.error(f"Error getting active cameras: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_cameras_by_status(self, status: str) -> List[CameraConfig]:
        """Get cameras by status"""
        session = None
        try:
            session = self.Session()
            return session.query(CameraConfig).filter(CameraConfig.status == status).all()
        except Exception as e:
            self.logger.error(f"Error getting cameras by status {status}: {e}")
            return []
        finally:
            if session:
                session.close()

    def update_camera(self, camera_id: int, update_data: dict) -> Optional[CameraConfig]:
        """Update camera configuration"""
        session = None
        try:
            session = self.Session()
            camera = session.query(CameraConfig).filter(CameraConfig.camera_id == camera_id).first()
            
            if not camera:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(camera, field) and value is not None:
                    setattr(camera, field, value)
            
            session.commit()
            session.refresh(camera)
            
            self.logger.info(f"Updated camera {camera_id}")
            return camera
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error updating camera {camera_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def delete_camera(self, camera_id: int) -> bool:
        """Delete camera configuration"""
        session = None
        try:
            session = self.Session()
            camera = session.query(CameraConfig).filter(CameraConfig.camera_id == camera_id).first()
            
            if not camera:
                return False
            
            session.delete(camera)
            session.commit()
            
            self.logger.info(f"Deleted camera {camera_id}")
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error deleting camera {camera_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    def activate_camera(self, camera_id: int, is_active: bool = True) -> bool:
        """Activate or deactivate a camera"""
        session = None
        try:
            session = self.Session()
            camera = session.query(CameraConfig).filter(CameraConfig.camera_id == camera_id).first()
            
            if not camera:
                return False
            
            camera.is_active = is_active
            camera.status = 'active' if is_active else 'inactive'
            
            session.commit()
            
            self.logger.info(f"{'Activated' if is_active else 'Deactivated'} camera {camera_id}")
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error activating camera {camera_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    # Tripwire Management Methods
    def create_tripwire(self, camera_id: int, tripwire_data: dict) -> Optional[Tripwire]:
        """Create a new tripwire for a camera"""
        session = None
        try:
            session = self.Session()
            
            # Verify camera exists
            camera = session.query(CameraConfig).filter(CameraConfig.camera_id == camera_id).first()
            if not camera:
                return None
            
            tripwire = Tripwire(
                camera_id=camera_id,
                name=tripwire_data['name'],
                position=tripwire_data['position'],
                spacing=tripwire_data.get('spacing', 0.01),
                direction=tripwire_data['direction'],
                detection_type=tripwire_data.get('detection_type', 'entry'),
                is_active=tripwire_data.get('is_active', True)
            )
            
            session.add(tripwire)
            session.commit()
            session.refresh(tripwire)
            
            self.logger.info(f"Created tripwire {tripwire.id} for camera {camera_id}")
            return tripwire
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error creating tripwire for camera {camera_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_camera_tripwires(self, camera_id: int) -> List[Tripwire]:
        """Get all tripwires for a camera"""
        session = None
        try:
            session = self.Session()
            return session.query(Tripwire).filter(Tripwire.camera_id == camera_id).all()
        except Exception as e:
            self.logger.error(f"Error getting tripwires for camera {camera_id}: {e}")
            return []
        finally:
            if session:
                session.close()

    def update_tripwire(self, tripwire_id: int, update_data: dict) -> Optional[Tripwire]:
        """Update tripwire configuration"""
        session = None
        try:
            session = self.Session()
            tripwire = session.query(Tripwire).filter(Tripwire.id == tripwire_id).first()
            
            if not tripwire:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(tripwire, field) and value is not None:
                    setattr(tripwire, field, value)
            
            session.commit()
            session.refresh(tripwire)
            
            self.logger.info(f"Updated tripwire {tripwire_id}")
            return tripwire
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error updating tripwire {tripwire_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def delete_tripwire(self, tripwire_id: int) -> bool:
        """Delete tripwire"""
        session = None
        try:
            session = self.Session()
            tripwire = session.query(Tripwire).filter(Tripwire.id == tripwire_id).first()
            
            if not tripwire:
                return False
            
            session.delete(tripwire)
            session.commit()
            
            self.logger.info(f"Deleted tripwire {tripwire_id}")
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error deleting tripwire {tripwire_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    def bulk_create_cameras_from_discovery(self, discovered_cameras: List[dict]) -> List[CameraConfig]:
        """Bulk create cameras from discovery results"""
        session = None
        created_cameras = []
        
        try:
            session = self.Session()
            
            for camera_data in discovered_cameras:
                # Check if camera already exists by IP
                existing = session.query(CameraConfig).filter(
                    CameraConfig.ip_address == camera_data['ip_address']
                ).first()
                
                if existing:
                    self.logger.info(f"Camera at {camera_data['ip_address']} already exists, skipping")
                    continue
                
                # Get the next available camera_id
                max_camera_id = session.query(func.max(CameraConfig.camera_id)).scalar()
                next_camera_id = (max_camera_id + 1) if max_camera_id is not None else 1
                
                camera = CameraConfig(
                    camera_id=next_camera_id,
                    camera_name=f"Camera {camera_data['ip_address']}",
                    camera_type='general',
                    ip_address=camera_data['ip_address'],
                    stream_url=camera_data.get('stream_urls', [None])[0],
                    resolution_width=1920,
                    resolution_height=1080,
                    fps=30,
                    gpu_id=0,
                    status='discovered',
                    is_active=False,
                    manufacturer=camera_data.get('manufacturer', 'Unknown'),
                    model=camera_data.get('model', 'Unknown'),
                    firmware_version=camera_data.get('firmware_version', 'Unknown'),
                    onvif_supported=camera_data.get('onvif_supported', False)
                )
                
                session.add(camera)
                created_cameras.append(camera)
            
            session.commit()
            
            # Refresh all created cameras
            for camera in created_cameras:
                session.refresh(camera)
            
            self.logger.info(f"Bulk created {len(created_cameras)} cameras from discovery")
            return created_cameras
            
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error bulk creating cameras: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_attendance_records(self, employee_id: str = None, start_date: datetime = None, end_date: datetime = None, limit: int = 100) -> List[AttendanceLog]:
        session = None
        try:
            session = self.Session()
            query = session.query(AttendanceLog).filter(AttendanceLog.is_valid == True)
            if employee_id:
                query = query.filter(AttendanceLog.employee_id == employee_id)
            if start_date:
                query = query.filter(AttendanceLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AttendanceLog.timestamp <= end_date)
            query = query.order_by(desc(AttendanceLog.timestamp))
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting attendance records: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_latest_attendance_by_employee(self, employee_id: str, hours_back: int = 10) -> Optional[AttendanceLog]:
        session = None
        try:
            session = self.Session()
            time_threshold = datetime.now() - timedelta(hours=hours_back)
            return session.query(AttendanceLog).filter(
                and_(
                    AttendanceLog.employee_id == employee_id,
                    AttendanceLog.timestamp >= time_threshold,
                    AttendanceLog.is_valid == True)
            ).order_by(desc(AttendanceLog.timestamp)).first()
        except Exception as e:
            self.logger.error(f"Error getting latest attendance for {employee_id}: {e}")
            return None
        finally:
            if session:
                session.close()
    
    # 🔧 Implement similar pattern for other methods like store_tracking_record, cleanup_old_embeddings, log_system_event, create_role, get_role, create_user, get_user following the same session management.
    def delete_employee(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return False
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).delete()
            session.query(AttendanceLog).filter(AttendanceLog.employee_id == employee_id).delete()
            session.delete(employee)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def delete_embeddings(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).delete()
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def remove_embedding(self, embedding_id: int) -> bool:
        session = None
        try:
            session = self.Session()
            embedding = session.query(FaceEmbedding).filter(FaceEmbedding.id == embedding_id).first()
            if not embedding:
                return False
            session.delete(embedding)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def archive_embeddings(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).update({
                FaceEmbedding.is_active: False
            })
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    def get_user_by_username(self, username: str) -> Optional[UserAccount]:
        session = None
        try:
            session = self.Session()
            return session.query(UserAccount).filter(UserAccount.username == username).first()
        except Exception as e:
            self.logger.error(f"Error fetching user {username}: {e}")
            return None
        finally:
            if session:
                session.close()
    def update_user_status(self, user_id: int, new_status: str) -> bool:
        session = self.Session()
        try:
            user = session.query(UserAccount).filter(UserAccount.id == user_id).first()
            if not user:
                return False
            user.status = new_status
            session.commit()
            return True
        except:
            session.rollback()
            return False
        finally:
            session.close()