import json
import io
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

from app.config import settings


class GoogleDriveService:
    """Service for interacting with Google Drive API"""
    
    def __init__(self):
        self.encryption_key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
        self.fernet = Fernet(self.encryption_key)
    
    def encrypt_credentials(self, credentials_dict: dict) -> str:
        """Encrypt credentials for storage"""
        credentials_json = json.dumps(credentials_dict)
        encrypted = self.fernet.encrypt(credentials_json.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_creds: str) -> dict:
        """Decrypt stored credentials"""
        decrypted = self.fernet.decrypt(encrypted_creds.encode())
        return json.loads(decrypted.decode())
    
    def get_drive_service(self, encrypted_creds: str):
        """
        Get Google Drive service from Service Account credentials
        
        Args:
            encrypted_creds: Encrypted Service Account JSON credentials
        
        Returns:
            Google Drive service object
        """
        if not encrypted_creds:
            raise Exception("No credentials provided")
        
        credentials_dict = self.decrypt_credentials(encrypted_creds)
        
        try:
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            service = build('drive', 'v3', credentials=credentials)
            return service
        except Exception as e:
            raise Exception(f"Error creating service account credentials: {str(e)}")
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        encrypted_creds: str,
        folder_id: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Upload a file to Google Drive
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            mime_type: MIME type of the file
            encrypted_creds: Encrypted Service Account credentials
            folder_id: Optional folder ID to upload to
        
        Returns:
            Tuple of (file_id, file_size)
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            
            file_metadata = {'name': filename}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, size'
            ).execute()
            
            return file.get('id'), int(file.get('size', 0))
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    async def download_file(
        self,
        file_id: str,
        encrypted_creds: str
    ) -> bytes:
        """
        Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            encrypted_creds: Encrypted Service Account credentials
        
        Returns:
            File content as bytes
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            
            request = service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_buffer.seek(0)
            return file_buffer.read()
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error downloading file: {str(e)}")
    
    async def delete_file(
        self,
        file_id: str,
        encrypted_creds: str
    ) -> bool:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            encrypted_creds: Encrypted Service Account credentials
        
        Returns:
            True if successful
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            service.files().delete(fileId=file_id).execute()
            return True
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")
    
    async def get_file_metadata(
        self,
        file_id: str,
        encrypted_creds: str
    ) -> dict:
        """
        Get file metadata from Google Drive
        
        Args:
            file_id: Google Drive file ID
            encrypted_creds: Encrypted Service Account credentials
        
        Returns:
            File metadata dict
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            file = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime'
            ).execute()
            return file
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting file metadata: {str(e)}")
    
    def validate_credentials(self, credentials_dict: dict) -> bool:
        """
        Validate Service Account credentials by attempting to create a service
        
        Args:
            credentials_dict: Service Account credentials dictionary
        
        Returns:
            True if valid
        """
        try:
            encrypted = self.encrypt_credentials(credentials_dict)
            service = self.get_drive_service(encrypted)
            # Try to list files to validate
            service.files().list(pageSize=1).execute()
            return True
        except Exception:
            return False
    
    def list_folder_contents(
        self,
        folder_id: str,
        encrypted_creds: str
    ) -> list:
        """
        List all files and folders inside a specific folder
        
        Args:
            folder_id: Google Drive folder ID
            encrypted_creds: Encrypted Service Account credentials
        
        Returns:
            List of files/folders with metadata
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, iconLink)",
                orderBy="folder,name"
            ).execute()
            
            files = results.get('files', [])
            
            # Format response
            formatted_files = []
            for file in files:
                is_folder = file['mimeType'] == 'application/vnd.google-apps.folder'
                formatted_files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'mimeType': file['mimeType'],
                    'isFolder': is_folder,
                    'size': file.get('size', '0') if not is_folder else None,
                    'createdTime': file['createdTime'],
                    'modifiedTime': file['modifiedTime'],
                    'iconLink': file.get('iconLink', '')
                })
            
            return formatted_files
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error listing folder contents: {str(e)}")
    
    def create_folder_structure(
        self,
        parent_folder_id: str,
        encrypted_creds: str
    ) -> dict:
        """
        Create initial folder structure for document management
        
        Args:
            parent_folder_id: Parent folder ID where structure will be created
            encrypted_creds: Encrypted Service Account credentials
        
        Returns:
            Dictionary with created folder IDs
        """
        try:
            service = self.get_drive_service(encrypted_creds)
            
            # Define folder structure
            folders = [
                'Pendientes',
                'En Revisión',
                'Aprobados',
                'Rechazados',
                'Archivados'
            ]
            
            created_folders = {}
            
            for folder_name in folders:
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                }
                
                folder = service.files().create(
                    body=file_metadata,
                    fields='id, name'
                ).execute()
                
                created_folders[folder_name] = {
                    'id': folder['id'],
                    'name': folder['name']
                }
            
            return created_folders
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error creating folder structure: {str(e)}")


# Global instance
drive_service = GoogleDriveService()
