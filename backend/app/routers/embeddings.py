"""
Face embeddings management router
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import FaceEmbedding, MessageResponse, CurrentUser
from app.security import require_admin_or_above, get_current_active_user
from db.db_config import get_db
from db.db_models import FaceEmbedding as FaceEmbeddingModel, Employee as EmployeeModel

router = APIRouter(prefix="/embeddings", tags=["Face Embeddings"])

@router.get("/", response_model=List[FaceEmbedding])
async def list_embeddings(
    employee_id: str = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    List face embeddings (Admin+ only)
    """
    query = db.query(FaceEmbeddingModel).filter(FaceEmbeddingModel.is_active == True)
    
    if employee_id:
        query = query.filter(FaceEmbeddingModel.employee_id == employee_id)
    
    embeddings = query.all()
    return embeddings

@router.get("/{embedding_id}", response_model=FaceEmbedding)
async def get_embedding(
    embedding_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get specific face embedding (Admin+ only)
    """
    embedding = db.query(FaceEmbeddingModel).filter(
        FaceEmbeddingModel.id == embedding_id
    ).first()
    
    if not embedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face embedding not found"
        )
    
    return embedding

@router.delete("/{embedding_id}", response_model=MessageResponse)
async def delete_embedding(
    embedding_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Delete face embedding (Admin+ only)
    """
    embedding = db.query(FaceEmbeddingModel).filter(
        FaceEmbeddingModel.id == embedding_id
    ).first()
    
    if not embedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face embedding not found"
        )
    
    # Get employee name for response
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == embedding.employee_id
    ).first()
    
    # Soft delete
    embedding.is_active = False
    db.commit()
    
    employee_name = employee.name if employee else "Unknown"
    return MessageResponse(
        message=f"Face embedding deleted for employee '{employee_name}'"
    )

@router.get("/employee/{employee_id}", response_model=List[FaceEmbedding])
async def get_employee_embeddings(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get all face embeddings for a specific employee (Admin+ only)
    """
    # Check if employee exists
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    embeddings = db.query(FaceEmbeddingModel).filter(
        FaceEmbeddingModel.employee_id == employee_id,
        FaceEmbeddingModel.is_active == True
    ).all()
    
    return embeddings

@router.delete("/employee/{employee_id}/all", response_model=MessageResponse)
async def delete_all_employee_embeddings(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Delete all face embeddings for a specific employee (Admin+ only)
    """
    # Check if employee exists
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Soft delete all embeddings
    embeddings = db.query(FaceEmbeddingModel).filter(
        FaceEmbeddingModel.employee_id == employee_id,
        FaceEmbeddingModel.is_active == True
    ).all()
    
    if not embeddings:
        return MessageResponse(
            message=f"No active face embeddings found for employee '{employee.name}'"
        )
    
    for embedding in embeddings:
        embedding.is_active = False
    
    db.commit()
    
    return MessageResponse(
        message=f"All face embeddings deleted for employee '{employee.name}' ({len(embeddings)} embeddings)"
    )

@router.get("/stats/summary")
async def get_embeddings_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get face embeddings statistics (Admin+ only)
    """
    total_embeddings = db.query(FaceEmbeddingModel).filter(
        FaceEmbeddingModel.is_active == True
    ).count()
    
    total_employees = db.query(EmployeeModel).filter(
        EmployeeModel.is_active == True
    ).count()
    
    employees_with_embeddings = db.query(FaceEmbeddingModel.employee_id).filter(
        FaceEmbeddingModel.is_active == True
    ).distinct().count()
    
    employees_without_embeddings = total_employees - employees_with_embeddings
    
    return {
        "total_embeddings": total_embeddings,
        "total_employees": total_employees,
        "employees_with_embeddings": employees_with_embeddings,
        "employees_without_embeddings": employees_without_embeddings,
        "average_embeddings_per_employee": round(total_embeddings / max(employees_with_embeddings, 1), 2)
    }
