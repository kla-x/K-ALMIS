import asyncio
import time
from typing import List, Optional
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from fastapi import FastAPI

from ..models import ActivityLog
from ..database import SessionLocal
from ..schemas.main import LogLevel, ActionType

# Global variables
log_buffer: List[dict] = []
buffer_lock = asyncio.Lock()
BATCH_SIZE = 50
MAX_WAIT = 5.0  # 5 seconds
_background_task: Optional[asyncio.Task] = None
_shutdown_event = asyncio.Event()

class LoggingService:
    def __init__(self):
        self.buffer: List[dict] = []
        self.last_flush = time.time()
        self.lock = asyncio.Lock()
        self.running = True
        
    async def enqueue_log(
        self,
        user_id, 
        action: ActionType, 
        target_table=None, 
        target_id=None, 
        details=None, 
        level: LogLevel = LogLevel.INFO
    ):
        """Add log entry to buffer"""
        log_data = {
            "user_id": str(user_id) if user_id else None,
            "action": action.value,
            "target_table": target_table,
            "target_id": target_id,
            "log_level": level.value,
            "details": details,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        async with self.lock:
            self.buffer.append(log_data)
            
            # Check if we should flush immediately
            if len(self.buffer) >= BATCH_SIZE:
                await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Internal method to flush buffer to database"""
        if not self.buffer:
            return
            
        buffer_copy = self.buffer.copy()
        self.buffer.clear()
        self.last_flush = time.time()
        
        # Run database operation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._flush_to_db_sync, buffer_copy)
    
    def _flush_to_db_sync(self, buffer: List[dict]):
        """Synchronous database flush (runs in thread pool)"""
        if not buffer:
            return
            
        db: Session = SessionLocal()
        try:
            # Convert string values back to enums for database insertion
            for log_entry in buffer:
                log_entry["action"] = ActionType(log_entry["action"])
                log_entry["log_level"] = LogLevel(log_entry["log_level"])
                
            db.bulk_insert_mappings(ActivityLog, buffer)
            db.commit()
            print(f"✅ Inserted {len(buffer)} logs to database")
        except Exception as e:
            db.rollback()
            print(f"❌ Error inserting logs to database: {e}")
        finally:
            db.close()
    
    async def background_flush_task(self):
        """Background task that flushes buffer periodically"""
        print("🚀 Background logging task started")
        
        while self.running:
            try:
                await asyncio.sleep(1)  # Check every second
                
                current_time = time.time()
                async with self.lock:
                    # Flush if we have logs and enough time has passed
                    if self.buffer and (current_time - self.last_flush >= MAX_WAIT):
                        await self._flush_buffer()
                        
            except asyncio.CancelledError:
                print("📝 Background logging task cancelled")
                break
            except Exception as e:
                print(f"❌ Error in background flush task: {e}")
                await asyncio.sleep(1)
        
        # Final flush on shutdown
        async with self.lock:
            if self.buffer:
                print("🔄 Final flush on shutdown...")
                await self._flush_buffer()
        
        print("✅ Background logging task completed")
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False

# Global logging service instance
logging_service = LoggingService()

# Public API functions
async def enqueue_log(
    user_id, 
    action: ActionType, 
    target_table=None, 
    target_id=None, 
    details=None, 
    level: LogLevel = LogLevel.INFO
):
    """Public function to enqueue a log entry"""
    await logging_service.enqueue_log(
        user_id, action, target_table, target_id, details, level
    )

# FastAPI Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""
    # Startup
    print("🚀 Starting logging service...")
    background_task = asyncio.create_task(logging_service.background_flush_task())
    
    yield  # Application runs here
    
    # Shutdown
    print("🛑 Shutting down logging service...")
    await logging_service.shutdown()
    background_task.cancel()
    
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Logging service shutdown complete")

# Alternative: If you prefer the old @app.on_event style
def setup_background_logging(app: FastAPI):
    """Alternative setup function for older FastAPI versions"""
    global _background_task
    
    @app.on_event("startup")
    async def startup_event():
        global _background_task
        print("🚀 Starting background logging...")
        _background_task = asyncio.create_task(logging_service.background_flush_task())
    
    @app.on_event("shutdown")
    async def shutdown_event():
        global _background_task
        print("🛑 Shutting down background logging...")
        await logging_service.shutdown()
        
        if _background_task:
            _background_task.cancel()
            try:
                await _background_task
            except asyncio.CancelledError:
                pass
        
        print("✅ Background logging shutdown complete")

