"""
Storage abstraction layer - supports local file system and Cloudflare R2.

For Railway production: use Cloudflare R2 (S3-compatible)
For local dev: use /tmp/utm-videos
"""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Storage configuration from environment
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" or "r2"
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")  # https://YOUR_ACCOUNT.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "creative-optimizer-videos")

# R2 Buckets for different access levels
R2_MARKET_BENCHMARKS_BUCKET = os.getenv("R2_MARKET_BENCHMARKS_BUCKET", "market-benchmarks")  # Public
R2_CLIENT_ASSETS_BUCKET = os.getenv("R2_CLIENT_ASSETS_BUCKET", "client-assets")  # Private

# Local storage path
LOCAL_STORAGE_PATH = "/tmp/utm-videos"


class StorageAdapter:
    """Abstract storage adapter supporting local and R2."""

    def __init__(self):
        # Debug: log environment variables (masked)
        logger.info(f"🔍 Storage initialization:")
        logger.info(f"   R2_ENDPOINT_URL: {R2_ENDPOINT_URL[:30] + '...' if R2_ENDPOINT_URL else 'NOT SET'}")
        logger.info(f"   R2_ACCESS_KEY_ID: {'***' + R2_ACCESS_KEY_ID[-4:] if R2_ACCESS_KEY_ID else 'NOT SET'}")
        logger.info(f"   R2_SECRET_ACCESS_KEY: {'***' + R2_SECRET_ACCESS_KEY[-4:] if R2_SECRET_ACCESS_KEY else 'NOT SET'}")

        # Auto-detect: use R2 if credentials are available, otherwise local
        if all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
            self.storage_type = "r2"
            # Initialize S3 client for R2
            self.s3_client = boto3.client(
                's3',
                endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name='auto'  # R2 uses 'auto'
            )
            self.bucket_name = R2_BUCKET_NAME
            logger.info(f"✅ Cloudflare R2 storage initialized (auto-detected)")
            logger.info(f"   Buckets: {R2_MARKET_BENCHMARKS_BUCKET} (public), {R2_CLIENT_ASSETS_BUCKET} (private)")
        else:
            # Fallback to local storage
            self.storage_type = "local"
            os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
            logger.warning(f"⚠️  R2 credentials not found. Using local storage: {LOCAL_STORAGE_PATH}")
            logger.warning(f"   Set R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY to use Cloudflare R2")

    def upload_video(self, file_content: bytes, filename: str) -> str:
        """
        Upload video to storage.

        Args:
            file_content: Video file bytes
            filename: Original filename

        Returns:
            URL or path to uploaded video
        """
        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        if self.storage_type == "r2":
            return self._upload_to_r2(file_content, unique_filename)
        else:
            return self._upload_to_local(file_content, unique_filename)

    def _upload_to_r2(self, file_content: bytes, filename: str) -> str:
        """Upload to Cloudflare R2."""
        try:
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"videos/{filename}",
                Body=file_content,
                ContentType="video/mp4"
            )

            # Generate public URL (assuming bucket is public or you have custom domain)
            # For R2, you typically set up a custom domain like videos.yourdomain.com
            public_url = f"{R2_ENDPOINT_URL}/{self.bucket_name}/videos/{filename}"

            logger.info(f"✅ Video uploaded to R2: {filename}")
            return public_url

        except ClientError as e:
            logger.error(f"R2 upload failed: {e}")
            # Fallback to local
            logger.warning("Falling back to local storage")
            return self._upload_to_local(file_content, filename)

    def _upload_to_local(self, file_content: bytes, filename: str) -> str:
        """Upload to local filesystem."""
        file_path = os.path.join(LOCAL_STORAGE_PATH, filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"✅ Video saved locally: {filename}")
        return file_path

    def get_video_url(self, path_or_url: str) -> str:
        """
        Get publicly accessible video URL.

        For R2: returns CDN URL
        For local: returns file:// path (for dev only)
        """
        if path_or_url.startswith("http"):
            return path_or_url
        else:
            # Local file - in production you'd serve this via nginx
            return f"file://{path_or_url}"

    def generate_presigned_upload_url(self, filename: str, expiration: int = 3600) -> dict:
        """
        Generate presigned URL for direct upload from frontend to R2.

        Args:
            filename: Original filename
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            {
                "upload_url": "https://...",
                "file_key": "videos/uuid.mp4",
                "public_url": "https://..."
            }
        """
        if self.storage_type != "r2":
            raise ValueError("Presigned URLs only available for R2 storage")

        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_key = f"videos/{unique_filename}"

        try:
            # Generate presigned POST URL (better for uploads)
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                ExpiresIn=expiration,
                Conditions=[
                    ["content-length-range", 1, 500*1024*1024],  # 1 byte to 500MB
                ],
            )

            # Public URL after upload
            public_url = f"{R2_ENDPOINT_URL}/{self.bucket_name}/{file_key}"

            logger.info(f"✅ Generated presigned upload URL: {file_key}")

            return {
                "upload_url": presigned_post['url'],
                "fields": presigned_post['fields'],
                "file_key": file_key,
                "public_url": public_url,
                "expires_in": expiration
            }

        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise

    def delete_video(self, path_or_url: str) -> bool:
        """Delete video from storage."""
        if self.storage_type == "r2" and path_or_url.startswith("http"):
            # Extract key from URL
            key = path_or_url.split(f"{self.bucket_name}/")[-1]
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"✅ Deleted from R2: {key}")
                return True
            except ClientError as e:
                logger.error(f"R2 delete failed: {e}")
                return False
        else:
            # Local file
            if os.path.exists(path_or_url):
                os.remove(path_or_url)
                logger.info(f"✅ Deleted local file: {path_or_url}")
                return True
            return False

    def upload_benchmark(self, file_content: bytes, filename: str, metadata: dict = None) -> str:
        """
        Upload benchmark video to PUBLIC market-benchmarks bucket.

        Benchmarks are:
        - Accessible to ALL users (public read)
        - Used for Market Intelligence
        - Stored in dedicated bucket

        Args:
            file_content: Video file bytes
            filename: Original filename
            metadata: Optional metadata (source_platform, cvr, etc.)

        Returns:
            Public URL to video
        """
        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"benchmark_{uuid.uuid4()}{file_ext}"

        if self.storage_type == "r2":
            return self._upload_benchmark_to_r2(file_content, unique_filename, metadata)
        else:
            # Local storage fallback
            return self._upload_to_local(file_content, unique_filename)

    def _upload_benchmark_to_r2(self, file_content: bytes, filename: str, metadata: dict = None) -> str:
        """Upload benchmark to R2 market-benchmarks bucket (PUBLIC)."""
        try:
            # Upload to PUBLIC benchmark bucket
            extra_args = {
                "ContentType": "video/mp4",
                "ACL": "public-read",  # Make publicly accessible
            }

            if metadata:
                extra_args["Metadata"] = {
                    k: str(v) for k, v in metadata.items()
                }

            self.s3_client.put_object(
                Bucket=R2_MARKET_BENCHMARKS_BUCKET,
                Key=f"videos/{filename}",
                Body=file_content,
                **extra_args
            )

            # Generate public URL (assuming custom domain or R2 public URL)
            public_url = f"{R2_ENDPOINT_URL}/{R2_MARKET_BENCHMARKS_BUCKET}/videos/{filename}"

            logger.info(f"✅ Benchmark uploaded to PUBLIC R2: {filename}")
            return public_url

        except ClientError as e:
            logger.error(f"R2 benchmark upload failed: {e}")
            # Fallback to local
            return self._upload_to_local(file_content, filename)

    def upload_client_video(self, file_content: bytes, filename: str, user_id: str) -> str:
        """
        Upload client video to PRIVATE client-assets bucket.

        Client videos are:
        - Accessible ONLY to the owner (via presigned URLs)
        - Protected by JWT authentication
        - Stored in private bucket

        Args:
            file_content: Video file bytes
            filename: Original filename
            user_id: User UUID (for namespacing)

        Returns:
            Private URL or path (requires presigned URL for access)
        """
        # Generate unique filename with user namespace
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"client_{user_id}/{uuid.uuid4()}{file_ext}"

        if self.storage_type == "r2":
            return self._upload_client_to_r2(file_content, unique_filename)
        else:
            # Local storage fallback
            return self._upload_to_local(file_content, unique_filename)

    def _upload_client_to_r2(self, file_content: bytes, filename: str) -> str:
        """Upload client video to R2 client-assets bucket (PRIVATE)."""
        try:
            # Upload to PRIVATE client bucket
            self.s3_client.put_object(
                Bucket=R2_CLIENT_ASSETS_BUCKET,
                Key=f"videos/{filename}",
                Body=file_content,
                ContentType="video/mp4"
                # No ACL - private by default
            )

            # Return internal reference (not public URL)
            # Access requires presigned URL via API endpoint
            internal_key = f"r2://{R2_CLIENT_ASSETS_BUCKET}/videos/{filename}"

            logger.info(f"✅ Client video uploaded to PRIVATE R2: {filename}")
            return internal_key

        except ClientError as e:
            logger.error(f"R2 client upload failed: {e}")
            # Fallback to local
            return self._upload_to_local(file_content, filename)

    def generate_client_video_access_url(self, internal_key: str, expiration: int = 3600) -> str:
        """
        Generate temporary presigned URL for client video access.

        Args:
            internal_key: r2://client-assets/videos/client_uuid/file.mp4
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            Presigned URL for temporary access
        """
        if not internal_key.startswith("r2://"):
            # Local file or already public URL
            return internal_key

        # Parse internal key
        parts = internal_key.replace("r2://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': key
                },
                ExpiresIn=expiration
            )

            logger.info(f"✅ Generated presigned URL (expires in {expiration}s)")
            return presigned_url

        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return internal_key  # Fallback to internal key

    def get_upload_url(self, user_id: str, filename: str, expiration: int = 3600) -> dict:
        """
        Generate presigned PUT URL for direct client video upload to R2.

        Frontend uses this URL to upload videos directly to client-assets bucket,
        bypassing the backend server (saves bandwidth and processing time).

        Args:
            user_id: User UUID (for namespacing videos by user)
            filename: Original filename (e.g., "my-video.mp4")
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            {
                "upload_url": "https://...",  # PUT request here
                "file_key": "videos/client_{user_id}/uuid.mp4",
                "internal_key": "r2://client-assets/videos/...",  # Save this in DB
                "expires_in": 3600
            }

        Example frontend usage:
            ```javascript
            const { upload_url, internal_key } = await getUploadUrl("video.mp4");
            await fetch(upload_url, {
                method: 'PUT',
                body: videoFile,
                headers: { 'Content-Type': 'video/mp4' }
            });
            // Save internal_key to backend
            ```
        """
        if self.storage_type != "r2":
            raise ValueError("Presigned upload URLs only available for R2 storage")

        # Generate unique filename with user namespace
        file_ext = os.path.splitext(filename)[1] or ".mp4"
        unique_filename = f"client_{user_id}/{uuid.uuid4()}{file_ext}"
        file_key = f"videos/{unique_filename}"

        try:
            # Generate presigned PUT URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': R2_CLIENT_ASSETS_BUCKET,
                    'Key': file_key,
                    'ContentType': 'video/mp4'
                },
                ExpiresIn=expiration
            )

            # Internal reference for DB storage
            internal_key = f"r2://{R2_CLIENT_ASSETS_BUCKET}/{file_key}"

            logger.info(f"✅ Generated presigned PUT URL for client upload: {file_key}")

            return {
                "upload_url": presigned_url,
                "file_key": file_key,
                "internal_key": internal_key,
                "expires_in": expiration,
                "bucket": R2_CLIENT_ASSETS_BUCKET
            }

        except ClientError as e:
            logger.error(f"Presigned PUT URL generation failed: {e}")
            raise

    def get_file_content(self, internal_key: str) -> Optional[bytes]:
        """
        Download file content from R2 storage.

        Used by video analyzer to download videos for Claude Vision analysis.

        Args:
            internal_key: r2://client-assets/videos/... or r2://market-benchmarks/...

        Returns:
            File content as bytes, or None if failed

        Example:
            video_content = storage.get_file_content('r2://client-assets/videos/...')
        """
        if not internal_key.startswith('r2://'):
            logger.error(f"Invalid R2 path: {internal_key}")
            return None

        try:
            # Parse bucket and key from r2://bucket/key
            parts = internal_key.replace('r2://', '').split('/', 1)
            if len(parts) != 2:
                logger.error(f"Invalid R2 path format: {internal_key}")
                return None

            bucket_name, object_key = parts

            # Download from R2
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            content = response['Body'].read()
            logger.info(f"✅ Downloaded {len(content)} bytes from R2: {internal_key}")
            return content

        except Exception as e:
            logger.error(f"Failed to download from R2: {e}")
            return None

    def get_download_url(self, internal_key: str, expiration: int = 3600) -> str:
        """
        Get presigned download URL for video playback.

        Wrapper around generate_client_video_access_url() with clearer naming.
        Used by frontend video player to display client videos.

        Args:
            internal_key: r2://client-assets/videos/client_uuid/file.mp4
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            Presigned GET URL for video playback

        Example:
            ```javascript
            const videoUrl = await getDownloadUrl(creative.video_url);
            <video src={videoUrl} controls />
            ```
        """
        return self.generate_client_video_access_url(internal_key, expiration)


# Singleton instance
_storage_adapter: Optional[StorageAdapter] = None


def get_storage() -> StorageAdapter:
    """Get storage adapter singleton."""
    global _storage_adapter
    if _storage_adapter is None:
        _storage_adapter = StorageAdapter()
    return _storage_adapter
