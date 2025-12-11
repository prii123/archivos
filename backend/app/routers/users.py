from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db import get_db
from app.schemas import UserResponse, UserUpdate, AdminResponse, UserAdminAssociation
from app.auth import get_current_user, get_admin_user
from app import crud
from app.models import User, RoleEnum

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    update_dict = user_data.model_dump(exclude_unset=True)
    
    # Users can't change their own role
    if 'role' in update_dict:
        del update_dict['role']
    
    updated_user = await crud.update_user(db, current_user.id, **update_dict)
    return updated_user


@router.get("/me/admins", response_model=List[AdminResponse])
async def get_my_admins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all admins associated with current user"""
    admins = await crud.get_user_admins(db, current_user.id)
    return admins


@router.post("/associate-admin", status_code=status.HTTP_200_OK)
async def associate_with_admin(
    association: UserAdminAssociation,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Associate a user with an admin (admin or superadmin only)"""
    success = await crud.associate_user_with_admin(
        db,
        user_id=association.user_id,
        admin_id=association.admin_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or Admin not found"
        )
    
    return {"message": "User associated with admin successfully"}


@router.delete("/disassociate-admin", status_code=status.HTTP_200_OK)
async def disassociate_from_admin(
    association: UserAdminAssociation,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Disassociate a user from an admin (admin or superadmin only)"""
    success = await crud.disassociate_user_from_admin(
        db,
        user_id=association.user_id,
        admin_id=association.admin_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or Admin not found"
        )
    
    return {"message": "User disassociated from admin successfully"}


@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin or superadmin only)"""
    users = await crud.list_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin or superadmin only)"""
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin or superadmin only)"""
    update_dict = user_data.model_dump(exclude_unset=True)
    
    updated_user = await crud.update_user(db, user_id, **update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin or superadmin only)"""
    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None
