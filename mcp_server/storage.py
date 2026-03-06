import aiosqlite
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from mcp_server.models import Source, Document, SourceStatus, SourceType

class Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    async def init(self):
        """Initialize database and create tables"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    name TEXT,
                    config TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_indexed_at TIMESTAMP,
                    document_count INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    file_path TEXT,
                    content_hash TEXT,
                    chunk_count INTEGER,
                    indexed_at TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS index_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            """)

            await db.commit()

    async def add_source(self, source: Source):
        """Add a new source"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sources (
                    id, type, url, name, config, status,
                    created_at, document_count, chunk_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.id,
                source.type.value,
                source.url,
                source.name,
                json.dumps(source.config) if source.config else None,
                source.status.value,
                source.created_at.isoformat(),
                source.document_count,
                source.chunk_count
            ))
            await db.commit()

    async def add_document(self, document: Document):
        """Add a new document"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO documents (
                    id, source_id, file_path, content_hash, chunk_count, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document.id,
                document.source_id,
                document.file_path,
                document.content_hash,
                document.chunk_count,
                document.indexed_at.isoformat() if document.indexed_at else None
            ))
            await db.commit()

    async def get_source(self, source_id: str) -> Optional[Source]:
        """Get source by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM sources WHERE id = ?",
                (source_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            return Source(
                id=row['id'],
                type=SourceType(row['type']),
                url=row['url'],
                name=row['name'],
                config=json.loads(row['config']) if row['config'] else None,
                status=SourceStatus(row['status']),
                error_message=row['error_message'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_indexed_at=datetime.fromisoformat(row['last_indexed_at']) if row['last_indexed_at'] else None,
                document_count=row['document_count'],
                chunk_count=row['chunk_count']
            )

    async def update_source_status(
        self,
        source_id: str,
        status: SourceStatus,
        error_message: Optional[str] = None
    ):
        """Update source status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sources
                SET status = ?, error_message = ?
                WHERE id = ?
            """, (status.value, error_message, source_id))
            await db.commit()

    async def list_sources(
        self,
        source_type: Optional[SourceType] = None
    ) -> List[Source]:
        """List all sources, optionally filtered by type"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if source_type:
                cursor = await db.execute(
                    "SELECT * FROM sources WHERE type = ? ORDER BY created_at DESC",
                    (source_type.value,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM sources ORDER BY created_at DESC"
                )

            rows = await cursor.fetchall()

            return [
                Source(
                    id=row['id'],
                    type=SourceType(row['type']),
                    url=row['url'],
                    name=row['name'],
                    config=json.loads(row['config']) if row['config'] else None,
                    status=SourceStatus(row['status']),
                    error_message=row['error_message'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_indexed_at=datetime.fromisoformat(row['last_indexed_at']) if row['last_indexed_at'] else None,
                    document_count=row['document_count'],
                    chunk_count=row['chunk_count']
                )
                for row in rows
            ]

    async def delete_source(self, source_id: str):
        """Delete a source and its documents"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            await db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            await db.commit()

    async def get_document_count(self) -> int:
        """Get total number of documents"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM documents") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0