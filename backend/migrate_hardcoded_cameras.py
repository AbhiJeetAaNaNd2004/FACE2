#!/usr/bin/env python3
"""
Migration script to convert hardcoded camera configurations to database entries
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from db.db_manager import DatabaseManager
from db.db_config import create_tables
from core.fts_system import TripwireConfig, CameraConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardcoded cameras to migrate (from original fts_system.py)
HARDCODED_CAMERAS = [
    {
        'camera_id': 0,
        'gpu_id': 0,
        'camera_type': 'entry',
        'resolution': (1280, 720),
        'fps': 15,
        'tripwires': [
            {
                'name': 'EntryDetection',
                'position': 0.755551,
                'spacing': 0.01,
                'direction': 'horizontal',
                'detection_type': 'entry'
            }
        ]
    },
    {
        'camera_id': 1,
        'gpu_id': 0,
        'camera_type': 'exit',
        'resolution': (1280, 720),
        'fps': 15,
        'tripwires': [
            {
                'name': 'EntryDetection',
                'position': 0.5,
                'spacing': 0.01,
                'direction': 'vertical',
                'detection_type': 'entry'
            }
        ]
    }
]

def migrate_hardcoded_cameras():
    """
    Migrate existing hardcoded cameras to database entries
    """
    logger.info("Starting migration of hardcoded cameras to database")
    
    try:
        # Ensure database tables exist
        create_tables()
        logger.info("Database tables created/verified")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        migrated_count = 0
        skipped_count = 0
        
        for camera_data in HARDCODED_CAMERAS:
            camera_id = camera_data['camera_id']
            
            # Check if camera already exists
            existing_camera = db_manager.get_camera(camera_id)
            if existing_camera:
                logger.info(f"Camera {camera_id} already exists in database, skipping")
                skipped_count += 1
                continue
            
            # Create camera configuration
            db_camera_data = {
                'camera_id': camera_id,
                'camera_name': f"Camera {camera_id} ({camera_data['camera_type'].title()})",
                'camera_type': camera_data['camera_type'],
                'resolution_width': camera_data['resolution'][0],
                'resolution_height': camera_data['resolution'][1],
                'fps': camera_data['fps'],
                'gpu_id': camera_data['gpu_id'],
                'status': 'active',
                'is_active': True,
                'location_description': f"Migrated {camera_data['camera_type']} camera",
                'manufacturer': 'Unknown',
                'model': 'Migrated Camera',
                'onvif_supported': False
            }
            
            # Create camera in database
            db_camera = db_manager.create_camera(db_camera_data)
            
            if db_camera:
                logger.info(f"Created camera {camera_id}: {db_camera.camera_name}")
                
                # Create tripwires
                tripwire_count = 0
                for tripwire_data in camera_data.get('tripwires', []):
                    tripwire = db_manager.create_tripwire(camera_id, tripwire_data)
                    if tripwire:
                        logger.info(f"  Created tripwire: {tripwire.name}")
                        tripwire_count += 1
                    else:
                        logger.error(f"  Failed to create tripwire: {tripwire_data['name']}")
                
                logger.info(f"  Created {tripwire_count} tripwires for camera {camera_id}")
                migrated_count += 1
            else:
                logger.error(f"Failed to create camera {camera_id}")
        
        logger.info(f"Migration completed: {migrated_count} cameras migrated, {skipped_count} skipped")
        
        # Verify migration
        verify_migration(db_manager)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def verify_migration(db_manager: DatabaseManager):
    """
    Verify that the migration was successful
    """
    logger.info("Verifying migration...")
    
    try:
        # Get all cameras
        all_cameras = db_manager.get_all_cameras()
        logger.info(f"Total cameras in database: {len(all_cameras)}")
        
        # Get active cameras
        active_cameras = db_manager.get_active_cameras()
        logger.info(f"Active cameras in database: {len(active_cameras)}")
        
        # Check each migrated camera
        for camera in active_cameras:
            logger.info(f"Camera {camera.camera_id}: {camera.camera_name}")
            logger.info(f"  Type: {camera.camera_type}")
            logger.info(f"  Resolution: {camera.resolution_width}x{camera.resolution_height}")
            logger.info(f"  FPS: {camera.fps}")
            logger.info(f"  Status: {camera.status}")
            logger.info(f"  Active: {camera.is_active}")
            
            # Check tripwires
            tripwires = db_manager.get_camera_tripwires(camera.camera_id)
            logger.info(f"  Tripwires: {len(tripwires)}")
            for tripwire in tripwires:
                logger.info(f"    - {tripwire.name}: {tripwire.direction} at {tripwire.position}")
        
        logger.info("Migration verification completed successfully")
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        raise

def rollback_migration():
    """
    Rollback the migration by removing migrated cameras
    """
    logger.info("Rolling back migration...")
    
    try:
        db_manager = DatabaseManager()
        
        rollback_count = 0
        for camera_data in HARDCODED_CAMERAS:
            camera_id = camera_data['camera_id']
            
            # Check if camera exists
            existing_camera = db_manager.get_camera(camera_id)
            if existing_camera:
                # Delete camera (will cascade delete tripwires)
                success = db_manager.delete_camera(camera_id)
                if success:
                    logger.info(f"Deleted camera {camera_id}")
                    rollback_count += 1
                else:
                    logger.error(f"Failed to delete camera {camera_id}")
            else:
                logger.info(f"Camera {camera_id} not found in database")
        
        logger.info(f"Rollback completed: {rollback_count} cameras removed")
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise

def main():
    """
    Main function with command line argument handling
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate hardcoded cameras to database")
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the migration'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing migration'
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    elif args.verify_only:
        db_manager = DatabaseManager()
        verify_migration(db_manager)
    else:
        migrate_hardcoded_cameras()

if __name__ == "__main__":
    main()