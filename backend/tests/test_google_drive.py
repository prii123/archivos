import pytest
from unittest.mock import Mock, patch
from app.google_drive import GoogleDriveService


@pytest.fixture
def drive_service():
    """Create a GoogleDriveService instance"""
    return GoogleDriveService()


def test_encrypt_decrypt_credentials(drive_service):
    """Test credential encryption and decryption"""
    test_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key": "test-key"
    }
    
    # Encrypt
    encrypted = drive_service.encrypt_credentials(test_creds)
    assert isinstance(encrypted, str)
    assert encrypted != str(test_creds)
    
    # Decrypt
    decrypted = drive_service.decrypt_credentials(encrypted)
    assert decrypted == test_creds


@pytest.mark.asyncio
async def test_upload_file_mock(drive_service):
    """Test file upload with mocked Google Drive API"""
    with patch.object(drive_service, 'get_drive_service') as mock_service:
        # Mock the Drive service
        mock_files = Mock()
        mock_create = Mock()
        mock_execute = Mock(return_value={'id': 'test-file-id', 'size': '1024'})
        
        mock_create.execute = mock_execute
        mock_files.create.return_value = mock_create
        mock_service.return_value.files.return_value = mock_files
        
        # Test credentials
        test_creds = {"type": "service_account", "project_id": "test"}
        encrypted = drive_service.encrypt_credentials(test_creds)
        
        # Upload file
        file_content = b"test file content"
        file_id, file_size = await drive_service.upload_file(
            file_content=file_content,
            filename="test.txt",
            mime_type="text/plain",
            encrypted_creds=encrypted,
            cred_type="service_account"
        )
        
        assert file_id == 'test-file-id'
        assert file_size == 1024


def test_validate_credentials_invalid(drive_service):
    """Test credential validation with invalid credentials"""
    invalid_creds = {"invalid": "credentials"}
    is_valid = drive_service.validate_credentials(invalid_creds, "service_account")
    assert is_valid == False
