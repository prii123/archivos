from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import io

from app.db import get_db
from app.schemas import FileResponse, FileListResponse, CommentCreate, CommentResponse, CommentUpdate
from app.auth import get_current_user
from app import crud
from app.models import User
from app.google_drive import drive_service

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    admin_id: int = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file to Google Drive"""
    # Get user's admins
    user_admins = await crud.get_user_admins(db, current_user.id)
    
    if not user_admins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any admin. Please contact an administrator."
        )
    
    # If admin_id provided, verify it's in user's admins
    if admin_id:
        admin = next((a for a in user_admins if a.id == admin_id), None)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not associated with this admin"
            )
    else:
        # Use first admin by default
        admin = user_admins[0]
    
    # Check if admin has Drive credentials configured
    if not admin.encrypted_drive_cred or not admin.drive_cred_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin has not configured Google Drive credentials"
        )
    
    # Read file content
    file_content = await file.read()
    
    try:
        # Upload to Google Drive
        drive_file_id, file_size = await drive_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type or 'application/octet-stream',
            encrypted_creds=admin.encrypted_drive_cred,
            cred_type=admin.drive_cred_type,
            folder_id=admin.drive_folder_id
        )
        
        # Create database record
        db_file = await crud.create_file(
            db=db,
            filename=file.filename,
            original_filename=file.filename,
            owner_admin_id=admin.id,
            uploaded_by_user_id=current_user.id,
            drive_file_id=drive_file_id,
            mime_type=file.content_type,
            file_size=file_size,
            description=description
        )
        
        return db_file
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    admin_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List files (filtered by user's admins for regular users)"""
    # If user is not admin/superadmin, only show files from their admins
    if current_user.role.value == "user":
        user_admins = await crud.get_user_admins(db, current_user.id)
        admin_ids = [a.id for a in user_admins]
        
        if admin_id and admin_id not in admin_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not associated with this admin"
            )
        
        # Get files for user's admins
        all_files = []
        for aid in admin_ids:
            if admin_id is None or aid == admin_id:
                files = await crud.list_files(db, admin_id=aid, skip=skip, limit=limit)
                all_files.extend(files)
        
        return FileListResponse(files=all_files, total=len(all_files))
    else:
        # Admin/Superadmin can see all files or filtered by admin_id
        files = await crud.list_files(db, admin_id=admin_id, skip=skip, limit=limit)
        return FileListResponse(files=files, total=len(files))


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get file metadata"""
    file = await crud.get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access
    if current_user.role.value == "user":
        user_admins = await crud.get_user_admins(db, current_user.id)
        admin_ids = [a.id for a in user_admins]
        if file.owner_admin_id not in admin_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download file from Google Drive"""
    file = await crud.get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access
    if current_user.role.value == "user":
        user_admins = await crud.get_user_admins(db, current_user.id)
        admin_ids = [a.id for a in user_admins]
        if file.owner_admin_id not in admin_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get admin
    admin = await crud.get_admin_by_id(db, file.owner_admin_id)
    if not admin or not admin.encrypted_drive_cred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin Drive credentials not configured"
        )
    
    try:
        # Download from Google Drive
        file_content = await drive_service.download_file(
            file_id=file.drive_file_id,
            encrypted_creds=admin.encrypted_drive_cred,
            cred_type=admin.drive_cred_type
        )
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=file.mime_type or 'application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{file.filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete file"""
    file = await crud.get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions (only uploader or admin can delete)
    if current_user.role.value == "user" and file.uploaded_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get admin
    admin = await crud.get_admin_by_id(db, file.owner_admin_id)
    if admin and admin.encrypted_drive_cred and file.drive_file_id:
        try:
            # Delete from Google Drive
            await drive_service.delete_file(
                file_id=file.drive_file_id,
                encrypted_creds=admin.encrypted_drive_cred,
                cred_type=admin.drive_cred_type
            )
        except Exception as e:
            # Log error but continue with DB deletion
            print(f"Error deleting from Drive: {str(e)}")
    
    # Delete from database
    await crud.delete_file(db, file_id)
    return None


# Comments endpoints
@router.post("/{file_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    file_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add comment to file"""
    file = await crud.get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access
    if current_user.role.value == "user":
        user_admins = await crud.get_user_admins(db, current_user.id)
        admin_ids = [a.id for a in user_admins]
        if file.owner_admin_id not in admin_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    comment = await crud.create_comment(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        text=comment_data.text
    )
    return comment


@router.get("/{file_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List comments for file"""
    file = await crud.get_file_by_id(db, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access
    if current_user.role.value == "user":
        user_admins = await crud.get_user_admins(db, current_user.id)
        admin_ids = [a.id for a in user_admins]
        if file.owner_admin_id not in admin_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    comments = await crud.list_file_comments(db, file_id)
    return comments


@router.patch("/{file_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    file_id: int,
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update comment"""
    comment = await crud.get_comment_by_id(db, comment_id)
    if not comment or comment.file_id != file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only comment author can update
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own comments"
        )
    
    updated_comment = await crud.update_comment(
        db=db,
        comment_id=comment_id,
        text=comment_data.text,
        user_id=current_user.id
    )
    return updated_comment


@router.delete("/{file_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    file_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete comment"""
    comment = await crud.get_comment_by_id(db, comment_id)
    if not comment or comment.file_id != file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only comment author or admin can delete
    if comment.user_id != current_user.id and current_user.role.value == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await crud.delete_comment(db, comment_id, current_user.id)
    return None
