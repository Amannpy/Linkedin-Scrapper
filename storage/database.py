"""SQLite database handler"""
import logging
import aiosqlite
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import config

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.db_path
        self.connection = None

    async def connect(self):
        """Connect to database"""
        self.connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info(f"✓ Connected to database: {self.db_path}")

    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def _create_tables(self):
        """Create database tables"""
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT,
                headline TEXT,
                location TEXT,
                data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                content TEXT,
                metrics TEXT,
                data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.connection.commit()

    async def save_profile(self, profile_data: Dict):
        """Save profile to database"""
        import json

        await self.connection.execute('''
            INSERT OR REPLACE INTO profiles (url, name, headline, location, data, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            profile_data.get('url'),
            profile_data.get('name'),
            profile_data.get('headline'),
            profile_data.get('location'),
            json.dumps(profile_data),
            datetime.now().isoformat()
        ))

        await self.connection.commit()

    async def get_profile(self, url: str) -> Optional[Dict]:
        """Get profile from database"""
        import json

        async with self.connection.execute(
                'SELECT data FROM profiles WHERE url = ?', (url,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None
