"""
Video storage manager для креативов.

Поддерживает:
- Cloudflare R2 (рекомендуется - дешево, egress free)
- DigitalOcean Spaces
- AWS S3
- Локальное хранилище

Workflow:
1. Upload видео в хранилище
2. Получить временную ссылку для скачивания
3. Скачать локально для анализа
4. Удалить локальную копию после анализа
"""

import os
import boto3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)


class VideoStorage:
    """
    Менеджер хранилища для видео креативов.

    Supports S3-compatible storage:
    - Cloudflare R2 (cheapest)
    - DigitalOcean Spaces
    - AWS S3
    """

    def __init__(self):
        """
        Initialize storage client from environment variables.

        Required env vars:
        - STORAGE_TYPE: r2, spaces, s3, or local
        - STORAGE_ENDPOINT: S3 endpoint (for R2/Spaces)
        - STORAGE_ACCESS_KEY: Access key
        - STORAGE_SECRET_KEY: Secret key
        - STORAGE_BUCKET: Bucket name
        - STORAGE_REGION: Region (optional)
        """

        self.storage_type = os.getenv("STORAGE_TYPE", "local")
        self.bucket_name = os.getenv("STORAGE_BUCKET", "utm-videos")
        self.local_path = os.getenv("STORAGE_LOCAL_PATH", "/tmp/utm-videos")

        if self.storage_type == "local":
            # Local storage (for MVP)
            Path(self.local_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Using local storage: {self.local_path}")

        else:
            # S3-compatible storage
            endpoint = os.getenv("STORAGE_ENDPOINT")
            access_key = os.getenv("STORAGE_ACCESS_KEY")
            secret_key = os.getenv("STORAGE_SECRET_KEY")
            region = os.getenv("STORAGE_REGION", "auto")

            if not all([endpoint, access_key, secret_key]):
                logger.warning(
                    "S3 credentials not set. Falling back to local storage."
                )
                self.storage_type = "local"
                Path(self.local_path).mkdir(parents=True, exist_ok=True)
                return

            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )

            logger.info(
                f"Using {self.storage_type} storage: "
                f"bucket={self.bucket_name}, endpoint={endpoint}"
            )

    def upload(
        self,
        file_path: str,
        creative_id: str,
        user_id: str
    ) -> str:
        """
        Upload video to storage.

        Args:
            file_path: Local path to video file
            creative_id: Creative UUID
            user_id: User UUID

        Returns:
            str: Storage key (path in bucket)

        Example:
            storage_key = storage.upload(
                file_path="/tmp/video.mp4",
                creative_id="uuid-123",
                user_id="user-456"
            )
            # Returns: "user-456/creatives/uuid-123.mp4"
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Generate storage key
        file_ext = Path(file_path).suffix
        storage_key = f"{user_id}/creatives/{creative_id}{file_ext}"

        if self.storage_type == "local":
            # Local storage: copy file
            dest_path = os.path.join(self.local_path, storage_key)
            Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

            import shutil
            shutil.copy2(file_path, dest_path)

            logger.info(f"Video uploaded locally: {dest_path}")

        else:
            # S3-compatible: upload to bucket
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                storage_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )

            logger.info(f"Video uploaded to {self.storage_type}: {storage_key}")

        return storage_key

    def download(
        self,
        storage_key: str,
        local_path: Optional[str] = None
    ) -> str:
        """
        Download video from storage to local temp file.

        Args:
            storage_key: Storage key (from upload())
            local_path: Optional local path (default: temp file)

        Returns:
            str: Local path to downloaded file

        Example:
            local_path = storage.download("user-456/creatives/uuid-123.mp4")
            # Returns: "/tmp/tmpXXXXXX.mp4"
        """

        if local_path is None:
            # Create temp file
            file_ext = Path(storage_key).suffix
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_ext
            )
            local_path = temp_file.name
            temp_file.close()

        if self.storage_type == "local":
            # Local storage: copy from local path
            source_path = os.path.join(self.local_path, storage_key)

            if not os.path.exists(source_path):
                raise FileNotFoundError(f"File not found: {source_path}")

            import shutil
            shutil.copy2(source_path, local_path)

        else:
            # S3-compatible: download from bucket
            self.s3_client.download_file(
                self.bucket_name,
                storage_key,
                local_path
            )

        logger.info(f"Video downloaded: {storage_key} → {local_path}")

        return local_path

    def get_url(
        self,
        storage_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate presigned URL for video.

        Args:
            storage_key: Storage key
            expires_in: URL expiration in seconds (default: 1 hour)

        Returns:
            str: Presigned URL

        Example:
            url = storage.get_url("user-456/creatives/uuid-123.mp4")
            # Returns: "https://r2.cloudflare.com/...?signature=..."
        """

        if self.storage_type == "local":
            # Local storage: return file:// URL
            local_path = os.path.join(self.local_path, storage_key)
            return f"file://{local_path}"

        else:
            # S3-compatible: generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key
                },
                ExpiresIn=expires_in
            )

            return url

    def delete(self, storage_key: str) -> bool:
        """
        Delete video from storage.

        Args:
            storage_key: Storage key

        Returns:
            bool: Success

        Example:
            storage.delete("user-456/creatives/uuid-123.mp4")
        """

        try:
            if self.storage_type == "local":
                # Local storage: delete file
                local_path = os.path.join(self.local_path, storage_key)
                if os.path.exists(local_path):
                    os.remove(local_path)

            else:
                # S3-compatible: delete from bucket
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_key
                )

            logger.info(f"Video deleted: {storage_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete video {storage_key}: {e}")
            return False

    def cleanup_temp_file(self, file_path: str):
        """
        Delete temporary file after analysis.

        Args:
            file_path: Path to temp file

        Example:
            # After analysis
            storage.cleanup_temp_file(local_path)
        """

        try:
            if os.path.exists(file_path) and file_path.startswith("/tmp"):
                os.remove(file_path)
                logger.debug(f"Temp file cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")


# Global instance
_storage = None


def get_video_storage() -> VideoStorage:
    """
    Get global VideoStorage instance.

    Usage:
    ```python
    from utils.video_storage import get_video_storage

    storage = get_video_storage()
    storage_key = storage.upload("/tmp/video.mp4", creative_id, user_id)
    ```
    """

    global _storage

    if _storage is None:
        _storage = VideoStorage()

    return _storage
