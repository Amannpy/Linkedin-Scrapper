"""Media download manager"""
import logging
import hashlib
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional

from config.settings import config

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Download and manage media files"""

    def __init__(self, download_dir: Optional[str] = None):
        self.download_dir = Path(download_dir or config.download_dir)
        self.download_dir.mkdir(exist_ok=True, parents=True)
        self.max_size_bytes = config.max_image_size_mb * 1024 * 1024

    async def download_image(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """Download image from URL"""
        if not filename:
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"img_{url_hash}.jpg"

        filepath = self.download_dir / filename

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        # Check size
                        content_length = response.headers.get('Content-Length')
                        if content_length and int(content_length) > self.max_size_bytes:
                            logger.warning(f"Image too large: {url}")
                            return None

                        # Download
                        content = await response.read()

                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)

                        logger.info(f"✓ Downloaded: {filename}")
                        return str(filepath)

        except Exception as e:
            logger.warning(f"Download failed for {url}: {e}")

        return None

    async def download_video(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """Download video from URL"""
        if not config.download_videos:
            logger.debug("Video download disabled")
            return None

        # Similar to image download but for videos
        # Implementation would be similar to download_image
        logger.warning("Video download not fully implemented")
        return None
