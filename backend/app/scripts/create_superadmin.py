"""Script to create superadmin user"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.config import settings
from app import crud
from app.models import RoleEnum


async def create_superadmin():
    """Create superadmin user if not exists"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if superadmin exists
            superadmin = await crud.get_user_by_email(db, settings.SUPERADMIN_EMAIL)
            
            if superadmin:
                print(f"Superadmin already exists: {settings.SUPERADMIN_EMAIL}")
                return
            
            # Create superadmin
            superadmin = await crud.create_user(
                db,
                email=settings.SUPERADMIN_EMAIL,
                password=settings.SUPERADMIN_PASSWORD,
                role=RoleEnum.SUPERADMIN
            )
            
            print(f"✅ Superadmin created successfully!")
            print(f"   Email: {superadmin.email}")
            print(f"   Role: {superadmin.role.value}")
            print(f"\n⚠️  IMPORTANT: Change the default password after first login!")
            
        except Exception as e:
            print(f"❌ Error creating superadmin: {str(e)}")
            raise


if __name__ == "__main__":
    print("Creating superadmin user...")
    asyncio.run(create_superadmin())
