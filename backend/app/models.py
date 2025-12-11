from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db import Base


class RoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Association table for many-to-many relationship between users and admins
user_admins = Table(
    'user_admins',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('admin_id', Integer, ForeignKey('admins.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum, values_callable=lambda x: [e.value for e in x]), default=RoleEnum.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    admin_profile = relationship("Admin", back_populates="user", uselist=False, cascade="all, delete-orphan")
    uploaded_files = relationship("File", back_populates="uploader", foreign_keys="File.uploaded_by_user_id")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    comment_actions = relationship("CommentHistory", back_populates="actor", foreign_keys="CommentHistory.actor_user_id")
    
    # Many-to-many with admins
    assigned_admins = relationship(
        "Admin",
        secondary=user_admins,
        back_populates="assigned_users"
    )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)  # Link to User (admin/superadmin)
    name = Column(String, nullable=False)
    encrypted_drive_cred = Column(Text, nullable=True)  # Encrypted JSON with Service Account credentials
    drive_folder_id = Column(String, nullable=True)  # Google Drive folder ID for document management
    
    # Folder structure IDs for quick navigation
    folder_pendientes_id = Column(String, nullable=True)
    folder_en_revision_id = Column(String, nullable=True)
    folder_aprobados_id = Column(String, nullable=True)
    folder_rechazados_id = Column(String, nullable=True)
    folder_archivados_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="admin_profile")
    files = relationship("File", back_populates="owner_admin", cascade="all, delete-orphan")
    
    # Many-to-many with users
    assigned_users = relationship(
        "User",
        secondary=user_admins,
        back_populates="assigned_admins"
    )


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    drive_file_id = Column(String, nullable=True, index=True)  # Google Drive file ID
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    owner_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner_admin = relationship("Admin", back_populates="files")
    uploader = relationship("User", back_populates="uploaded_files", foreign_keys=[uploaded_by_user_id])
    comments = relationship("Comment", back_populates="file", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    file = relationship("File", back_populates="comments")
    user = relationship("User", back_populates="comments")
    history = relationship("CommentHistory", back_populates="comment", cascade="all, delete-orphan")


class CommentHistory(Base):
    __tablename__ = "comment_history"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete='CASCADE'), nullable=False)
    action = Column(String, nullable=False)  # 'created', 'edited', 'deleted'
    previous_text = Column(Text, nullable=True)
    new_text = Column(Text, nullable=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    comment = relationship("Comment", back_populates="history")
    actor = relationship("User", back_populates="comment_actions", foreign_keys=[actor_user_id])
