from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import RoleEnum


# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: RoleEnum = RoleEnum.USER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[RoleEnum] = None


class UserRoleUpdate(BaseModel):
    role: RoleEnum


class UserResponse(UserBase):
    id: int
    role: RoleEnum
    created_at: datetime
    
    class Config:
        from_attributes = True


# Admin Schemas
class AdminBase(BaseModel):
    name: str


class AdminCreate(AdminBase):
    pass


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    drive_folder_id: Optional[str] = None


class AdminResponse(AdminBase):
    id: int
    user_id: int
    drive_folder_id: Optional[str] = None
    has_drive_credentials: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class DriveCredentialsCreate(BaseModel):
    """Schema for creating/updating Google Drive Service Account credentials"""
    service_account_json: str = Field(..., min_length=10)  # Service account JSON file content
    drive_folder_id: str = Field(..., min_length=1)  # Required: Google Drive folder ID


class DriveCredentialsResponse(BaseModel):
    """Schema for Drive credentials response (without sensitive data)"""
    drive_folder_id: Optional[str] = None
    has_credentials: bool = False
    client_email: Optional[str] = None  # Service account email for confirmation





# File Schemas
class FileBase(BaseModel):
    filename: str
    description: Optional[str] = None


class FileCreate(FileBase):
    pass


class FileResponse(FileBase):
    id: int
    original_filename: str
    drive_file_id: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    owner_admin_id: int
    uploaded_by_user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int


# Comment Schemas
class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    file_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentHistoryResponse(BaseModel):
    id: int
    comment_id: int
    action: str
    previous_text: Optional[str]
    new_text: Optional[str]
    actor_user_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# User-Admin Association
class UserAdminAssociation(BaseModel):
    user_id: int
    admin_id: int


# Settings/Configuration
class SystemSettings(BaseModel):
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
