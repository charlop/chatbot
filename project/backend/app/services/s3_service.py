"""
S3 Service - PDF Streaming from S3 with Redis Caching.

Handles:
- Streaming PDFs from S3 with IAM authentication
- Redis caching (TTL: 15 minutes)
- Error handling for S3 operations
"""

import io
import logging
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from redis.asyncio import Redis

from app.config import settings
from app.utils.cache import get_redis

logger = logging.getLogger(__name__)


class S3ServiceError(Exception):
    """Base exception for S3 service errors."""

    pass


class S3ObjectNotFoundError(S3ServiceError):
    """Raised when S3 object not found."""

    pass


class S3AccessDeniedError(S3ServiceError):
    """Raised when access to S3 object is denied."""

    pass


class S3Service:
    """
    Service for streaming PDFs from S3 with caching.

    Provides:
    - PDF streaming from S3 with IAM authentication
    - Redis caching to reduce S3 bandwidth costs
    - Comprehensive error handling
    """

    def __init__(self):
        """Initialize S3 client with IAM credentials."""
        self.s3_client = boto3.client(
            "s3",
            # Credentials are automatically discovered from:
            # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # 2. ~/.aws/credentials file
            # 3. IAM instance profile (when running on EC2/ECS)
        )
        self.cache_ttl = 900  # 15 minutes in seconds
        self.cache_key_prefix = "pdf"

    def _get_cache_key(self, bucket: str, key: str) -> str:
        """Generate Redis cache key for PDF."""
        # Use bucket:key as cache key to handle same keys across buckets
        return f"{self.cache_key_prefix}:{bucket}:{key}"

    async def get_pdf_stream(self, bucket: str, key: str) -> tuple[bytes, bool]:
        """
        Get PDF from S3 with caching.

        Args:
            bucket: S3 bucket name
            key: S3 object key (path to PDF)

        Returns:
            Tuple of (pdf_bytes, cache_hit)

        Raises:
            S3ObjectNotFoundError: If PDF not found in S3
            S3AccessDeniedError: If access to PDF is denied
            S3ServiceError: For other S3 errors
        """
        cache_key = self._get_cache_key(bucket, key)

        # Try Redis cache first
        redis = await get_redis()
        if redis:
            try:
                cached_pdf = await redis.get(cache_key)
                if cached_pdf:
                    logger.info(f"PDF cache HIT for s3://{bucket}/{key}")
                    return (cached_pdf, True)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}, falling back to S3")

        logger.info(f"PDF cache MISS for s3://{bucket}/{key}, fetching from S3")

        # Fetch from S3
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            pdf_bytes = response["Body"].read()

            # Cache in Redis (non-blocking)
            if redis:
                try:
                    await redis.setex(cache_key, self.cache_ttl, pdf_bytes)
                    logger.info(f"Cached PDF s3://{bucket}/{key} in Redis (TTL: {self.cache_ttl}s)")
                except Exception as e:
                    logger.warning(f"Redis cache write failed: {e}")

            return (pdf_bytes, False)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "NoSuchKey":
                logger.error(f"PDF not found in S3: s3://{bucket}/{key}")
                raise S3ObjectNotFoundError(f"PDF not found in S3: s3://{bucket}/{key}") from e

            elif error_code in ("403", "AccessDenied", "Forbidden"):
                logger.error(f"Access denied to PDF in S3: s3://{bucket}/{key}")
                raise S3AccessDeniedError(f"Access denied to PDF in S3: s3://{bucket}/{key}") from e

            else:
                logger.error(f"S3 error fetching PDF s3://{bucket}/{key}: {error_code}")
                raise S3ServiceError(f"S3 error: {error_code}") from e

        except NoCredentialsError as e:
            logger.error("AWS credentials not configured")
            raise S3ServiceError(
                "AWS credentials not configured. Please configure IAM credentials."
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error fetching PDF from S3: {e}")
            raise S3ServiceError(f"Unexpected S3 error: {str(e)}") from e

    async def invalidate_cache(self, bucket: str, key: str) -> None:
        """
        Invalidate cached PDF.

        Args:
            bucket: S3 bucket name
            key: S3 object key
        """
        cache_key = self._get_cache_key(bucket, key)

        redis = await get_redis()
        if redis:
            try:
                await redis.delete(cache_key)
                logger.info(f"Invalidated PDF cache for s3://{bucket}/{key}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")


# Singleton instance
_s3_service: S3Service | None = None


def get_s3_service() -> S3Service:
    """Get S3Service singleton instance."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
