"""Caching mechanism for scraped data"""
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

from config.settings import config

logger = logging.getLogger(__name__)


class Cache:
    """Simple file-based cache"""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or config.download_dir) / 'cache'
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.expiry_hours = config.cache_expiry_hours

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def set(self, key: str, value: Any):
        """Set cache value"""
        if not config.use_cache:
            return

        try:
            cache_data = {
                'value': value,
                'cached_at': datetime.now().isoformat()
            }

            cache_path = self._get_cache_path(key)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)

        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not config.use_cache:
            return None

        try:
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return None

            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check expiry
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_at > timedelta(hours=self.expiry_hours):
                cache_path.unlink()  # Remove expired cache
                return None

            return cache_data['value']

        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    def clear(self):
        """Clear all cache"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            logger.info("✓ Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
