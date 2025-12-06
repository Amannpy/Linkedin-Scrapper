"""CSV storage handler"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class CSVHandler:
    """Handle CSV file operations"""

    @staticmethod
    def save(data: List[Dict], filepath: str):
        """Save data to CSV file"""
        if not data:
            logger.warning("No data to save to CSV")
            return

        try:
            path = Path(filepath)
            path.parent.mkdir(exist_ok=True, parents=True)

            # Flatten nested data
            flattened = []
            for item in data:
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        flat_item[key] = json.dumps(value)
                    else:
                        flat_item[key] = value
                flattened.append(flat_item)

            # Write CSV
            if flattened:
                keys = flattened[0].keys()
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(flattened)

                logger.info(f"✓ Saved CSV to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            raise

    @staticmethod
    def load(filepath: str) -> List[Dict]:
        """Load data from CSV file"""
        try:
            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(dict(row))
            return data

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise
