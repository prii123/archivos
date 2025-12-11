from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.db import get_db
from app.schemas import (
    AdminCreate, AdminResponse, AdminUpdate,
    UserCreate, UserResponse, UserRoleUpdate
)
from app.auth import get_admin_user, get_superadmin_user
from app import crud
from app.models import User, RoleEnum
from app.google_drive import drive_service

router = APIRouter(prefix="/admin", tags=["Admin"])


# Admin Management (for all admins)
@router.get("/profile", response_model=AdminResponse)
async def get_admin_profile(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin profile based on user email"""
    admin = await crud.get_admin_by_email(db, current_user.email)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found. Please contact superadmin."
        )
    return admin


# Superadmin only endpoints
@router.get("/all", response_model=List[AdminResponse])
async def list_all_admins(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all admins (superadmin only)"""
    admins = await crud.list_admins(db, skip=skip, limit=limit)
    return admins


@router.post("/create", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new admin (superadmin only)"""
    # Check if admin already exists
    existing_admin = await crud.get_admin_by_email(db, admin_data.email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )
    
    # Create admin
    admin = await crud.create_admin(
        db,
        name=admin_data.name,
        email=admin_data.email
    )
    
    # Also create corresponding user with admin role if doesn't exist
    user = await crud.get_user_by_email(db, admin_data.email)
    if not user:
        # Create user with temporary password (they should change it)
        await crud.create_user(
            db,
            email=admin_data.email,
            password="ChangeMe123!",
            role=RoleEnum.ADMIN
        )
    else:
        # Update existing user to admin role
        await crud.update_user(db, user.id, role=RoleEnum.ADMIN)
    
    return admin


@router.patch("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update admin (superadmin only)"""
    update_dict = admin_data.model_dump(exclude_unset=True)
    
    admin = await crud.update_admin(db, admin_id, **update_dict)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return admin


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete admin (superadmin only)"""
    success = await crud.delete_admin(db, admin_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return None


@router.post("/users/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_as_admin(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new user (admin or superadmin only)"""
    # Check if user already exists
    existing_user = await crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Only superadmin can create admin/superadmin users
    if user_data.role in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        if current_user.role != RoleEnum.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin can create admin users"
            )
    
    user = await crud.create_user(
        db,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )
    
    return user


@router.get("/audit/users", response_model=List[UserResponse])
async def audit_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users for audit (superadmin only)"""
    users = await crud.list_users(db, skip=skip, limit=limit)
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user role (superadmin only)"""
    # Get user by ID
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent changing own role
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Update role
    updated_user = await crud.update_user(db, user_id, role=role_update.role)
    
    # If promoting to admin/superadmin, create admin profile if doesn't exist
    if role_update.role in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        admin = await crud.get_admin_by_user_id(db, user_id)
        if not admin:
            await crud.create_admin_profile(
                db,
                user_id=user_id,
                name=user.email.split('@')[0].capitalize()
            )
    
    return updated_user
