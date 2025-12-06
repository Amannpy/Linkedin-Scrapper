"""JSON storage handler"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class JSONHandler:
    """Handle JSON file operations"""

    @staticmethod
    def save(data: Any, filepath: str):
        """Save data to JSON file"""
        try:
            path = Path(filepath)
            path.parent.mkdir(exist_ok=True, parents=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved JSON to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            raise

    @staticmethod
    def load(filepath: str) -> Any:
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            raise

    @staticmethod
    def append(data: Dict, filepath: str):
        """Append data to JSON array file"""
        try:
            path = Path(filepath)

            # Load existing data
            if path.exists():
                existing = JSONHandler.load(filepath)
                if isinstance(existing, list):
                    existing.append(data)
                else:
                    existing = [existing, data]
            else:
                existing = [data]

            JSONHandler.save(existing, filepath)

        except Exception as e:
            logger.error(f"Failed to append to JSON: {e}")
            raise