from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models import User, Admin, File, Comment, CommentHistory, RoleEnum
from app.auth import get_password_hash


# User CRUD
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, role: RoleEnum = RoleEnum.USER) -> User:
    """Create new user"""
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        role=role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
    """Update user"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    if 'password' in kwargs:
        kwargs['password_hash'] = get_password_hash(kwargs.pop('password'))
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete user"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    return True


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """List users"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


# Admin CRUD
async def get_admin_by_user_id(db: AsyncSession, user_id: int) -> Optional[Admin]:
    """Get admin profile by user ID"""
    result = await db.execute(select(Admin).where(Admin.user_id == user_id))
    return result.scalar_one_or_none()


async def get_admin_by_id(db: AsyncSession, admin_id: int) -> Optional[Admin]:
    """Get admin by ID"""
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    return result.scalar_one_or_none()


async def create_admin_profile(db: AsyncSession, user_id: int, name: str) -> Admin:
    """Create admin profile for a user"""
    admin = Admin(user_id=user_id, name=name)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def update_admin(db: AsyncSession, admin_id: int, **kwargs) -> Optional[Admin]:
    """Update admin"""
    admin = await get_admin_by_id(db, admin_id)
    if not admin:
        return None
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(admin, key, value)
    
    admin.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(admin)
    return admin


async def delete_admin(db: AsyncSession, admin_id: int) -> bool:
    """Delete admin"""
    admin = await get_admin_by_id(db, admin_id)
    if not admin:
        return False
    
    await db.delete(admin)
    await db.commit()
    return True


async def list_admins(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Admin]:
    """List admins"""
    result = await db.execute(select(Admin).offset(skip).limit(limit))
    return result.scalars().all()


async def update_drive_credentials(
    db: AsyncSession, 
    user_id: int, 
    credentials_data: dict,
    drive_folder_id: str
) -> Optional[Admin]:
    """Update Google Drive Service Account credentials for admin/superadmin"""
    from app.google_drive import GoogleDriveService
    
    # Get or create admin profile
    admin = await get_admin_by_user_id(db, user_id)
    if not admin:
        # Get user to create profile
        user = await get_user_by_id(db, user_id)
        if not user:
            return None
        admin = await create_admin_profile(db, user_id, user.email.split('@')[0])
    
    # Encrypt credentials
    drive_service = GoogleDriveService()
    encrypted_cred = drive_service.encrypt_credentials(credentials_data)
    
    # Update admin
    admin.encrypted_drive_cred = encrypted_cred
    admin.drive_folder_id = drive_folder_id
    admin.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(admin)
    return admin


async def get_drive_credentials(db: AsyncSession, user_id: int) -> Optional[dict]:
    """Get decrypted Google Drive Service Account credentials for admin/superadmin"""
    from app.google_drive import GoogleDriveService
    
    admin = await get_admin_by_user_id(db, user_id)
    if not admin or not admin.encrypted_drive_cred:
        return None
    
    # Decrypt and return credentials
    drive_service = GoogleDriveService()
    credentials_data = drive_service.decrypt_credentials(admin.encrypted_drive_cred)
    return credentials_data


async def delete_drive_credentials(db: AsyncSession, user_id: int) -> bool:
    """Delete Google Drive credentials for admin/superadmin"""
    admin = await get_admin_by_user_id(db, user_id)
    if not admin:
        return False
    
    admin.encrypted_drive_cred = None
    admin.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


# User-Admin associations
async def associate_user_with_admin(db: AsyncSession, user_id: int, admin_id: int) -> bool:
    """Associate a user with an admin"""
    user = await get_user_by_id(db, user_id)
    admin = await get_admin_by_id(db, admin_id)
    
    if not user or not admin:
        return False
    
    if admin not in user.assigned_admins:
        user.assigned_admins.append(admin)
        await db.commit()
    
    return True


async def disassociate_user_from_admin(db: AsyncSession, user_id: int, admin_id: int) -> bool:
    """Disassociate a user from an admin"""
    user = await get_user_by_id(db, user_id)
    admin = await get_admin_by_id(db, admin_id)
    
    if not user or not admin:
        return False
    
    if admin in user.assigned_admins:
        user.assigned_admins.remove(admin)
        await db.commit()
    
    return True


async def get_user_admins(db: AsyncSession, user_id: int) -> List[Admin]:
    """Get all admins for a user"""
    result = await db.execute(
        select(User).options(selectinload(User.assigned_admins)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user.assigned_admins if user else []


# File CRUD
async def create_file(
    db: AsyncSession,
    filename: str,
    original_filename: str,
    owner_admin_id: int,
    uploaded_by_user_id: int,
    drive_file_id: Optional[str] = None,
    mime_type: Optional[str] = None,
    file_size: Optional[int] = None,
    description: Optional[str] = None
) -> File:
    """Create new file record"""
    file = File(
        filename=filename,
        original_filename=original_filename,
        owner_admin_id=owner_admin_id,
        uploaded_by_user_id=uploaded_by_user_id,
        drive_file_id=drive_file_id,
        mime_type=mime_type,
        file_size=file_size,
        description=description
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def get_file_by_id(db: AsyncSession, file_id: int) -> Optional[File]:
    """Get file by ID"""
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()


async def list_files(
    db: AsyncSession,
    user_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[File]:
    """List files with optional filtering"""
    query = select(File)
    
    if user_id:
        query = query.where(File.uploaded_by_user_id == user_id)
    
    if admin_id:
        query = query.where(File.owner_admin_id == admin_id)
    
    query = query.offset(skip).limit(limit).order_by(File.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def delete_file(db: AsyncSession, file_id: int) -> bool:
    """Delete file record"""
    file = await get_file_by_id(db, file_id)
    if not file:
        return False
    
    await db.delete(file)
    await db.commit()
    return True


# Comment CRUD
async def create_comment(db: AsyncSession, file_id: int, user_id: int, text: str) -> Comment:
    """Create new comment"""
    comment = Comment(file_id=file_id, user_id=user_id, text=text)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Create history entry
    history = CommentHistory(
        comment_id=comment.id,
        action='created',
        new_text=text,
        actor_user_id=user_id
    )
    db.add(history)
    await db.commit()
    
    return comment


async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Optional[Comment]:
    """Get comment by ID"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    return result.scalar_one_or_none()


async def update_comment(db: AsyncSession, comment_id: int, text: str, user_id: int) -> Optional[Comment]:
    """Update comment"""
    comment = await get_comment_by_id(db, comment_id)
    if not comment:
        return None
    
    previous_text = comment.text
    comment.text = text
    comment.updated_at = datetime.utcnow()
    
    # Create history entry
    history = CommentHistory(
        comment_id=comment.id,
        action='edited',
        previous_text=previous_text,
        new_text=text,
        actor_user_id=user_id
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(db: AsyncSession, comment_id: int, user_id: int) -> bool:
    """Delete comment"""
    comment = await get_comment_by_id(db, comment_id)
    if not comment:
        return False
    
    # Create history entry
    history = CommentHistory(
        comment_id=comment.id,
        action='deleted',
        previous_text=comment.text,
        actor_user_id=user_id
    )
    db.add(history)
    await db.commit()
    
    await db.delete(comment)
    await db.commit()
    return True


async def list_file_comments(db: AsyncSession, file_id: int) -> List[Comment]:
    """List comments for a file"""
    result = await db.execute(
        select(Comment).where(Comment.file_id == file_id).order_by(Comment.created_at)
    )
    return result.scalars().all()


async def get_comment_history(db: AsyncSession, comment_id: int) -> List[CommentHistory]:
    """Get history for a comment"""
    result = await db.execute(
        select(CommentHistory).where(CommentHistory.comment_id == comment_id).order_by(CommentHistory.timestamp)
    )
    return result.scalars().all()
