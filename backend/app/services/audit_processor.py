"""
Async Audit Processor Service

This service handles background processing of audit events from the audit queue.
It provides:
- Async audit queue processing
- Batch processing for performance
- Error handling and retry logic
- Audit log consolidation
- Performance monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit import AuditQueue, AuditProcessingStatus
from app.core.audit import AuditLog
from app.core.audit_mixins import ChangeDataCapture

logger = logging.getLogger(__name__)


class AuditProcessor:
    """
    Async audit processor for handling audit queue events.
    """
    
    def __init__(self, processor_name: str = "default_audit_processor", batch_size: int = 100):
        self.processor_name = processor_name
        self.batch_size = batch_size
        self.is_running = False
        self.processing_stats = {
            'processed_count': 0,
            'error_count': 0,
            'start_time': None,
            'last_batch_time': None
        }
    
    async def start_processing(self, db: Session):
        """Start the audit processor."""
        if self.is_running:
            logger.warning(f"Audit processor {self.processor_name} is already running")
            return
        
        self.is_running = True
        self.processing_stats['start_time'] = datetime.now(timezone.utc)
        
        # Initialize or update processor status
        await self._update_processor_status(db, 'active')
        
        logger.info(f"Starting audit processor: {self.processor_name}")
        
        try:
            while self.is_running:
                batch_processed = await self._process_batch(db)
                
                if batch_processed == 0:
                    # No pending items, wait before checking again
                    await asyncio.sleep(5)
                else:
                    # Continue processing immediately if there are more items
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Audit processor {self.processor_name} encountered error: {e}")
            await self._update_processor_status(db, 'error', str(e))
        finally:
            self.is_running = False
            logger.info(f"Audit processor {self.processor_name} stopped")
    
    async def stop_processing(self, db: Session):
        """Stop the audit processor."""
        self.is_running = False
        await self._update_processor_status(db, 'stopped')
        logger.info(f"Audit processor {self.processor_name} stop requested")
    
    async def _process_batch(self, db: Session) -> int:
        """Process a batch of audit queue entries."""
        try:
            # Get pending audit entries
            pending_entries = db.query(AuditQueue)\
                .filter_by(status='pending')\
                .order_by(AuditQueue.created_at)\
                .limit(self.batch_size)\
                .all()
            
            if not pending_entries:
                return 0
            
            processed_count = 0
            
            for entry in pending_entries:
                try:
                    # Mark as processing
                    entry.mark_processing()
                    db.commit()
                    
                    # Process the audit entry
                    await self._process_audit_entry(db, entry)
                    
                    # Mark as completed
                    entry.mark_completed()
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process audit entry {entry.id}: {e}")
                    entry.mark_failed(str(e))
                    self.processing_stats['error_count'] += 1
                
                finally:
                    db.commit()
            
            # Update processing stats
            self.processing_stats['processed_count'] += processed_count
            self.processing_stats['last_batch_time'] = datetime.now(timezone.utc)
            
            # Update processor status
            if processed_count > 0:
                last_processed_id = pending_entries[-1].id
                await self._update_processor_progress(db, last_processed_id)
            
            logger.debug(f"Processed batch of {processed_count} audit entries")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing audit batch: {e}")
            await self._update_processor_status(db, 'error', str(e))
            return 0
    
    async def _process_audit_entry(self, db: Session, entry: AuditQueue):
        """Process a single audit entry."""
        try:
            # Create consolidated audit log entry
            audit_log = AuditLog(
                table_name=entry.table_name,
                record_id=entry.record_id,
                action=entry.operation,
                old_values=entry.old_values,
                new_values=entry.new_values,
                user_id=entry.user_id,
                timestamp=entry.created_at,
                ip_address=entry.ip_address,
                user_agent=entry.user_agent
            )
            
            db.add(audit_log)
            
            # Create CDC log entry for real-time tracking
            change_data = self._build_change_data(entry)
            
            ChangeDataCapture.log_change(
                session=db,
                table_name=entry.table_name,
                record_id=entry.record_id,
                operation=entry.operation,
                change_data=change_data,
                user_id=entry.user_id,
                session_id=entry.session_id,
                source='audit_processor'
            )
            
            logger.debug(f"Processed audit entry for {entry.table_name}.{entry.record_id}")
            
        except Exception as e:
            logger.error(f"Failed to process audit entry {entry.id}: {e}")
            raise
    
    def _build_change_data(self, entry: AuditQueue) -> Dict[str, Any]:
        """Build change data structure for CDC logging."""
        change_data = {
            'operation': entry.operation,
            'timestamp': entry.created_at.isoformat(),
            'processor': self.processor_name
        }
        
        if entry.operation == 'INSERT':
            change_data['data'] = entry.new_values or {}
        elif entry.operation == 'UPDATE':
            change_data['changes'] = {}
            old_vals = entry.old_values or {}
            new_vals = entry.new_values or {}
            
            # Build field-level changes
            all_fields = set(old_vals.keys()) | set(new_vals.keys())
            for field in all_fields:
                old_val = old_vals.get(field)
                new_val = new_vals.get(field)
                if old_val != new_val:
                    change_data['changes'][field] = {
                        'old': old_val,
                        'new': new_val
                    }
        elif entry.operation == 'DELETE':
            change_data['data'] = entry.old_values or {}
        
        return change_data
    
    async def _update_processor_status(self, db: Session, status: str, error_message: str = None):
        """Update processor status in database."""
        try:
            processor_status = db.query(AuditProcessingStatus)\
                .filter_by(processor_name=self.processor_name)\
                .first()
            
            if not processor_status:
                processor_status = AuditProcessingStatus(
                    processor_name=self.processor_name,
                    status=status,
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(processor_status)
            else:
                processor_status.status = status
                processor_status.updated_at = datetime.now(timezone.utc)
                
                if error_message:
                    processor_status.mark_error(error_message)
                elif status == 'active':
                    processor_status.mark_active()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update processor status: {e}")
    
    async def _update_processor_progress(self, db: Session, last_processed_id: int):
        """Update processor progress."""
        try:
            processor_status = db.query(AuditProcessingStatus)\
                .filter_by(processor_name=self.processor_name)\
                .first()
            
            if processor_status:
                processor_status.update_progress(last_processed_id)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update processor progress: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        stats = self.processing_stats.copy()
        stats['processor_name'] = self.processor_name
        stats['is_running'] = self.is_running
        stats['batch_size'] = self.batch_size
        
        if stats['start_time']:
            runtime = datetime.now(timezone.utc) - stats['start_time']
            stats['runtime_seconds'] = int(runtime.total_seconds())
            
            if stats['processed_count'] > 0 and runtime.total_seconds() > 0:
                stats['processing_rate'] = round(stats['processed_count'] / runtime.total_seconds(), 2)
            else:
                stats['processing_rate'] = 0.0
        
        return stats


class AuditProcessorManager:
    """
    Manager for multiple audit processors.
    """
    
    def __init__(self):
        self.processors: Dict[str, AuditProcessor] = {}
        self.processor_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_processor(self, processor_name: str, batch_size: int = 100):
        """Start a new audit processor."""
        if processor_name in self.processors:
            logger.warning(f"Processor {processor_name} already exists")
            return
        
        processor = AuditProcessor(processor_name, batch_size)
        self.processors[processor_name] = processor
        
        # Start processor task
        db = next(get_db())
        task = asyncio.create_task(processor.start_processing(db))
        self.processor_tasks[processor_name] = task
        
        logger.info(f"Started audit processor: {processor_name}")
    
    async def stop_processor(self, processor_name: str):
        """Stop a specific audit processor."""
        if processor_name not in self.processors:
            logger.warning(f"Processor {processor_name} not found")
            return
        
        processor = self.processors[processor_name]
        db = next(get_db())
        await processor.stop_processing(db)
        
        # Cancel the task
        if processor_name in self.processor_tasks:
            task = self.processor_tasks[processor_name]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.processor_tasks[processor_name]
        
        del self.processors[processor_name]
        logger.info(f"Stopped audit processor: {processor_name}")
    
    async def stop_all_processors(self):
        """Stop all audit processors."""
        processor_names = list(self.processors.keys())
        for processor_name in processor_names:
            await self.stop_processor(processor_name)
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get statistics for all processors."""
        stats = {
            'total_processors': len(self.processors),
            'running_processors': sum(1 for p in self.processors.values() if p.is_running),
            'processors': {}
        }
        
        for name, processor in self.processors.items():
            stats['processors'][name] = processor.get_processing_stats()
        
        return stats
    
    async def retry_failed_entries(self, db: Session, max_retries: int = 3) -> int:
        """Retry failed audit entries that can be retried."""
        failed_entries = db.query(AuditQueue)\
            .filter_by(status='failed')\
            .filter(AuditQueue.retry_count < max_retries)\
            .all()
        
        retry_count = 0
        for entry in failed_entries:
            entry.status = 'pending'
            entry.error_message = None
            retry_count += 1
        
        db.commit()
        logger.info(f"Queued {retry_count} failed entries for retry")
        return retry_count
    
    async def cleanup_old_entries(self, db: Session, days_to_keep: int = 90) -> int:
        """Clean up old completed audit entries."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted_count = db.query(AuditQueue)\
            .filter_by(status='completed')\
            .filter(AuditQueue.processed_at < cutoff_date)\
            .delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old audit entries")
        return deleted_count


# Global processor manager instance
audit_processor_manager = AuditProcessorManager()


# Utility functions for audit processing

async def start_default_audit_processor():
    """Start the default audit processor."""
    await audit_processor_manager.start_processor("default_audit_processor", batch_size=100)


async def stop_all_audit_processors():
    """Stop all audit processors."""
    await audit_processor_manager.stop_all_processors()


def get_audit_processing_health(db: Session) -> Dict[str, Any]:
    """Get comprehensive audit processing health status."""
    # Get queue statistics
    pending_count = db.query(AuditQueue).filter_by(status='pending').count()
    processing_count = db.query(AuditQueue).filter_by(status='processing').count()
    failed_count = db.query(AuditQueue).filter_by(status='failed').count()
    
    # Get processor status
    processors = db.query(AuditProcessingStatus).all()
    active_processors = [p for p in processors if p.status == 'active']
    error_processors = [p for p in processors if p.status == 'error']
    
    # Calculate health score
    health_score = 100
    if pending_count > 1000:
        health_score -= 20
    if failed_count > 100:
        health_score -= 30
    if len(error_processors) > 0:
        health_score -= 25
    if len(active_processors) == 0:
        health_score -= 50
    
    health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
    
    return {
        'health_score': max(0, health_score),
        'health_status': health_status,
        'queue_stats': {
            'pending': pending_count,
            'processing': processing_count,
            'failed': failed_count
        },
        'processor_stats': {
            'total': len(processors),
            'active': len(active_processors),
            'error': len(error_processors)
        },
        'recommendations': _get_health_recommendations(pending_count, failed_count, len(active_processors))
    }


def _get_health_recommendations(pending_count: int, failed_count: int, active_processors: int) -> List[str]:
    """Get health recommendations based on current status."""
    recommendations = []
    
    if pending_count > 1000:
        recommendations.append("High pending queue - consider starting additional processors")
    
    if failed_count > 100:
        recommendations.append("High failure rate - investigate error patterns")
    
    if active_processors == 0:
        recommendations.append("No active processors - start audit processing immediately")
    
    if pending_count == 0 and failed_count == 0:
        recommendations.append("System healthy - audit processing up to date")
    
    return recommendations
