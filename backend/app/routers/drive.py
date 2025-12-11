"""Google Drive credentials management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import json

from app.db import get_db
from app.auth import get_current_user, require_role
from app.models import User, RoleEnum
from app import crud, schemas
from app.config import settings
from app.google_drive import drive_service

router = APIRouter(prefix="/drive", tags=["Google Drive"])


@router.post("/credentials", response_model=schemas.DriveCredentialsResponse)
async def set_drive_credentials(
    credentials: schemas.DriveCredentialsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set Google Drive Service Account credentials for the current admin/superadmin user.
    
    - **service_account_json**: The JSON file content from Google Cloud Console (Service Account key)
    - **drive_folder_id**: The Google Drive folder ID where documents will be managed
    
    The Service Account email must have access to the specified folder.
    """
    # Check if user has admin or superadmin role
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can configure Google Drive"
        )
    
    # Validate and parse Service Account JSON
    try:
        credentials_data = json.loads(credentials.service_account_json)
        
        # Validate required Service Account fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        missing_fields = [field for field in required_fields if field not in credentials_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Service Account JSON. Missing fields: {', '.join(missing_fields)}"
            )
        
        if credentials_data.get('type') != 'service_account':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON file must be a Service Account key (type: 'service_account')"
            )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    
    # Update credentials
    admin = await crud.update_drive_credentials(
        db=db,
        user_id=current_user.id,
        credentials_data=credentials_data,
        drive_folder_id=credentials.drive_folder_id
    )
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials"
        )
    
    return schemas.DriveCredentialsResponse(
        drive_folder_id=admin.drive_folder_id,
        has_credentials=True,
        client_email=credentials_data.get('client_email')
    )


@router.get("/credentials", response_model=schemas.DriveCredentialsResponse)
async def get_drive_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current Google Drive credentials status (without sensitive data).
    """
    # Check if user has admin or superadmin role
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can access Google Drive settings"
        )
    admin = await crud.get_admin_by_user_id(db, current_user.id)
    
    if not admin:
        return schemas.DriveCredentialsResponse(
            drive_folder_id=None,
            has_credentials=False,
            client_email=None
        )
    
    # Get client_email from credentials if available
    client_email = None
    if admin.encrypted_drive_cred:
        try:
            creds = await crud.get_drive_credentials(db, current_user.id)
            client_email = creds.get('client_email')
        except:
            pass
    
    return schemas.DriveCredentialsResponse(
        drive_folder_id=admin.drive_folder_id,
        has_credentials=bool(admin.encrypted_drive_cred),
        client_email=client_email
    )


@router.delete("/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drive_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete Google Drive credentials for the current user.
    """
    # Check if user has admin or superadmin role
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can delete Google Drive credentials"
        )
    success = await crud.delete_drive_credentials(db, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No credentials found"
        )
    
    return None


@router.put("/folder", response_model=schemas.DriveCredentialsResponse)
async def update_drive_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update only the Google Drive folder ID (keep existing credentials).
    """
    # Check if user has admin or superadmin role
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can update Google Drive folder"
        )
    admin = await crud.get_admin_by_user_id(db, current_user.id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found. Please set credentials first."
        )
    
    admin.drive_folder_id = folder_id
    await db.commit()
    await db.refresh(admin)
    
    # Get client_email
    client_email = None
    if admin.encrypted_drive_cred:
        try:
            creds = await crud.get_drive_credentials(db, current_user.id)
            client_email = creds.get('client_email')
        except:
            pass
    
    return schemas.DriveCredentialsResponse(
        drive_folder_id=admin.drive_folder_id,
        has_credentials=bool(admin.encrypted_drive_cred),
        client_email=client_email
    )


@router.get("/folder/contents")
async def list_folder_contents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all files and folders in the configured Drive folder"""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can access Drive contents"
        )
    
    try:
        # Get admin profile with credentials
        admin = await crud.get_admin_by_user_id(db, current_user.id)
        
        if not admin or not admin.encrypted_drive_cred:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Drive credentials configured. Please configure credentials first."
            )
        
        if not admin.drive_folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No folder ID configured"
            )
        
        # List folder contents using Service Account
        files = drive_service.list_folder_contents(
            folder_id=admin.drive_folder_id,
            encrypted_creds=admin.encrypted_drive_cred
        )
        
        return {
            "folder_id": admin.drive_folder_id,
            "total_items": len(files),
            "files": files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list folder contents: {str(e)}"
        )


@router.post("/folder/create-structure")
async def create_folder_structure(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create initial folder structure for document management"""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and superadmins can create folder structure"
        )
    
    try:
        # Get admin profile with credentials
        admin = await crud.get_admin_by_user_id(db, current_user.id)
        
        if not admin or not admin.encrypted_drive_cred:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Drive credentials configured"
            )
        
        if not admin.drive_folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No folder ID configured"
            )
        
        # Create folder structure using Service Account
        created_folders = drive_service.create_folder_structure(
            parent_folder_id=admin.drive_folder_id,
            encrypted_creds=admin.encrypted_drive_cred
        )
        
        # Save folder IDs to database for quick navigation
        admin.folder_pendientes_id = created_folders.get('Pendientes', {}).get('id')
        admin.folder_en_revision_id = created_folders.get('En Revisión', {}).get('id')
        admin.folder_aprobados_id = created_folders.get('Aprobados', {}).get('id')
        admin.folder_rechazados_id = created_folders.get('Rechazados', {}).get('id')
        admin.folder_archivados_id = created_folders.get('Archivados', {}).get('id')
        
        await db.commit()
        await db.refresh(admin)
        
        return {
            "message": "Folder structure created successfully",
            "folders": created_folders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder structure: {str(e)}"
        )
