# ~/Documents/WealthTrackr/backend/utils/file_utils.py

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
import magic  # python-magic for file type detection
from PIL import Image  # Pillow for image processing
from fastapi import UploadFile, HTTPException, status
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("static/uploads")
PROFILE_PICS_DIR = UPLOAD_DIR / "profile_pictures"
RECEIPTS_DIR = UPLOAD_DIR / "receipts" 
DOCUMENTS_DIR = UPLOAD_DIR / "documents"

# File size limits (in bytes)
MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_RECEIPT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'image/jpeg': '.jpg',
    'image/png': '.png'
}

# ─── Directory Setup ────────────────────────────────────────────────────────────
def ensure_upload_directories():
    """Create upload directories if they don't exist"""
    directories = [UPLOAD_DIR, PROFILE_PICS_DIR, RECEIPTS_DIR, DOCUMENTS_DIR]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

# Initialize directories on import
ensure_upload_directories()

# ─── File Validation Functions ──────────────────────────────────────────────────
def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """Validate file size"""
    try:
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > max_size:
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating file size: {e}")
        return False

def validate_file_type(file: UploadFile, allowed_types: dict) -> bool:
    """Validate file type using python-magic"""
    try:
        # Read a small chunk to determine file type
        chunk = file.file.read(1024)
        file.file.seek(0)  # Reset file position
        
        # Use python-magic to detect MIME type
        mime_type = magic.from_buffer(chunk, mime=True)
        
        return mime_type in allowed_types
    except Exception as e:
        logger.error(f"Error validating file type: {e}")
        return False

def validate_image_file(file: UploadFile) -> bool:
    """Comprehensive image file validation"""
    if not file:
        return False
    
    # Check file size
    if not validate_file_size(file, MAX_PROFILE_IMAGE_SIZE):
        logger.warning(f"Image file too large: {file.filename}")
        return False
    
    # Check file type
    if not validate_file_type(file, ALLOWED_IMAGE_TYPES):
        logger.warning(f"Invalid image file type: {file.filename}")
        return False
    
    # Additional image-specific validation
    try:
        # Try to open with PIL to ensure it's a valid image
        file.file.seek(0)
        image = Image.open(file.file)
        image.verify()  # Verify it's a valid image
        file.file.seek(0)  # Reset for later use
        
        # Check image dimensions (optional)
        width, height = image.size
        if width > 4000 or height > 4000:
            logger.warning(f"Image dimensions too large: {width}x{height}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating image file {file.filename}: {e}")
        return False

def validate_document_file(file: UploadFile) -> bool:
    """Validate document files (receipts, etc.)"""
    if not file:
        return False
    
    # Check file size
    if not validate_file_size(file, MAX_DOCUMENT_SIZE):
        return False
    
    # Check file type
    return validate_file_type(file, ALLOWED_DOCUMENT_TYPES)

# ─── File Processing Functions ──────────────────────────────────────────────────
def generate_unique_filename(original_filename: str, user_id: Optional[int] = None) -> str:
    """Generate a unique filename to prevent conflicts"""
    # Get file extension
    file_extension = Path(original_filename).suffix.lower()
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())
    
    # Include user_id if provided
    if user_id:
        filename = f"user_{user_id}_{unique_id}{file_extension}"
    else:
        filename = f"{unique_id}{file_extension}"
    
    return filename

def resize_profile_image(image_path: Path, max_size: tuple = (500, 500)) -> Path:
    """Resize profile image to optimize storage and loading"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG saving)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            optimized_path = image_path.parent / f"optimized_{image_path.name}"
            img.save(optimized_path, 'JPEG', quality=85, optimize=True)
            
            # Replace original with optimized version
            optimized_path.replace(image_path)
            
            return image_path
    except Exception as e:
        logger.error(f"Error resizing image {image_path}: {e}")
        return image_path  # Return original if optimization fails

# ─── Profile Picture Functions ──────────────────────────────────────────────────
async def save_profile_picture(file: UploadFile, user_id: int) -> str:
    """Save and process profile picture"""
    try:
        # Validate the image file
        if not validate_image_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Please upload a JPG, PNG, GIF, or WebP file under 5MB."
            )
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename, user_id)
        file_path = PROFILE_PICS_DIR / filename
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Optimize the image
        optimized_path = resize_profile_image(file_path)
        
        # Return URL path for storing in database
        relative_path = f"/static/uploads/profile_pictures/{filename}"
        
        logger.info(f"Profile picture saved for user {user_id}: {filename}")
        return relative_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving profile picture for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save profile picture"
        )

def delete_profile_picture(file_url: str) -> bool:
    """Delete profile picture from filesystem"""
    try:
        # Extract filename from URL
        filename = Path(file_url).name
        file_path = PROFILE_PICS_DIR / filename
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted profile picture: {filename}")
            return True
        else:
            logger.warning(f"Profile picture not found: {filename}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting profile picture {file_url}: {e}")
        return False

# ─── Receipt/Document Functions ─────────────────────────────────────────────────
async def save_receipt_file(file: UploadFile, user_id: int, expense_id: Optional[int] = None) -> str:
    """Save receipt file for expense tracking"""
    try:
        # Validate the document file
        if not validate_document_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload PDF, DOC, DOCX, TXT, JPG, or PNG files under 20MB."
            )
        
        # Generate unique filename
        base_name = f"receipt_{user_id}"
        if expense_id:
            base_name += f"_expense_{expense_id}"
        
        filename = generate_unique_filename(f"{base_name}_{file.filename}")
        file_path = RECEIPTS_DIR / filename
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL path for storing in database
        relative_path = f"/static/uploads/receipts/{filename}"
        
        logger.info(f"Receipt saved for user {user_id}: {filename}")
        return relative_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving receipt for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save receipt"
        )

async def save_document_file(file: UploadFile, user_id: int, document_type: str = "general") -> str:
    """Save general document file"""
    try:
        # Validate the document file
        if not validate_document_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type or size"
            )
        
        # Generate unique filename with document type
        base_name = f"{document_type}_{user_id}"
        filename = generate_unique_filename(f"{base_name}_{file.filename}")
        file_path = DOCUMENTS_DIR / filename
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL path for storing in database
        relative_path = f"/static/uploads/documents/{filename}"
        
        logger.info(f"Document saved for user {user_id}: {filename}")
        return relative_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving document for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document"
        )

def delete_file(file_url: str) -> bool:
    """Delete any uploaded file"""
    try:
        # Determine file type and directory from URL
        if "/profile_pictures/" in file_url:
            directory = PROFILE_PICS_DIR
        elif "/receipts/" in file_url:
            directory = RECEIPTS_DIR
        elif "/documents/" in file_url:
            directory = DOCUMENTS_DIR
        else:
            logger.warning(f"Unknown file type for URL: {file_url}")
            return False
        
        # Extract filename and delete
        filename = Path(file_url).name
        file_path = directory / filename
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {filename}")
            return True
        else:
            logger.warning(f"File not found: {filename}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting file {file_url}: {e}")
        return False

# ─── File Management Functions ──────────────────────────────────────────────────
def get_user_files(user_id: int, file_type: str = "all") -> List[dict]:
    """Get list of files for a user"""
    files = []
    
    try:
        directories = []
        if file_type in ["all", "profile"]:
            directories.append(("profile", PROFILE_PICS_DIR))
        if file_type in ["all", "receipts"]:
            directories.append(("receipts", RECEIPTS_DIR))
        if file_type in ["all", "documents"]:
            directories.append(("documents", DOCUMENTS_DIR))
        
        for file_type_name, directory in directories:
            for file_path in directory.glob(f"*user_{user_id}_*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "type": file_type_name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "url": f"/static/uploads/{file_type_name}/{file_path.name}"
                    })
        
        return files
        
    except Exception as e:
        logger.error(f"Error getting files for user {user_id}: {e}")
        return []

def cleanup_old_files(days_old: int = 30):
    """Clean up old temporary files"""
    try:
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        for directory in [UPLOAD_DIR, PROFILE_PICS_DIR, RECEIPTS_DIR, DOCUMENTS_DIR]:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Check if file is old and appears to be temporary
                    if (file_path.stat().st_mtime < cutoff_time and 
                        ("temp_" in file_path.name or "tmp_" in file_path.name)):
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path.name}")
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")

# ─── File URL Helpers ───────────────────────────────────────────────────────────
def get_full_url(relative_path: str, request_base_url: str) -> str:
    """Convert relative file path to full URL"""
    if relative_path.startswith('http'):
        return relative_path  # Already a full URL
    
    base_url = request_base_url.rstrip('/')
    relative_path = relative_path.lstrip('/')
    
    return f"{base_url}/{relative_path}"

def validate_file_access(file_url: str, user_id: int) -> bool:
    """Validate that user has access to the file"""
    try:
        # Extract filename and check if it belongs to the user
        filename = Path(file_url).name
        
        # Check if filename contains user_id (simple ownership check)
        return f"user_{user_id}_" in filename
        
    except Exception as e:
        logger.error(f"Error validating file access: {e}")
        return False

# ─── Batch Operations ───────────────────────────────────────────────────────────
def get_storage_usage(user_id: Optional[int] = None) -> dict:
    """Get storage usage statistics"""
    try:
        total_size = 0
        file_count = 0
        
        directories = [PROFILE_PICS_DIR, RECEIPTS_DIR, DOCUMENTS_DIR]
        
        for directory in directories:
            pattern = f"*user_{user_id}_*" if user_id else "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error calculating storage usage: {e}")
        return {"error": str(e)}
