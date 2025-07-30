"""
File Storage Retention Service

Service layer for file storage management including:
- File expiry and retention policy enforcement
- Storage quota management and monitoring
- Automated purge jobs for expired files
- File lifecycle management and archiving
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.exceptions import NotFoundError, ValidationError, StorageQuotaExceededError
from app.services.webhook_integration_service import WebhookTriggers
import logging
import os
import shutil
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class FileRetentionPolicy(str, Enum):
    TEMPORARY = "temporary"      # 7 days
    SHORT_TERM = "short_term"    # 30 days
    MEDIUM_TERM = "medium_term"  # 90 days
    LONG_TERM = "long_term"      # 365 days
    PERMANENT = "permanent"      # Never expires


class FileStorageRetentionService:
    """Service layer for file storage retention management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
        self.retention_policies = {
            FileRetentionPolicy.TEMPORARY: 7,
            FileRetentionPolicy.SHORT_TERM: 30,
            FileRetentionPolicy.MEDIUM_TERM: 90,
            FileRetentionPolicy.LONG_TERM: 365,
            FileRetentionPolicy.PERMANENT: None  # Never expires
        }
    
    def scan_expired_files(self) -> Dict[str, Any]:
        """Scan for files that have exceeded their retention period."""
        try:
            # Get all files with retention policies
            files_with_policies = self._get_files_with_retention_policies()
            
            expired_files = []
            expiring_soon = []
            now = datetime.now(timezone.utc)
            
            for file_record in files_with_policies:
                expiry_result = self._check_file_expiry(file_record, now)
                
                if expiry_result['status'] == 'expired':
                    expired_files.append({
                        'file_id': file_record['id'],
                        'file_path': file_record['file_path'],
                        'file_name': file_record['file_name'],
                        'size_bytes': file_record['size_bytes'],
                        'retention_policy': file_record['retention_policy'],
                        'created_at': file_record['created_at'],
                        'expired_since_days': expiry_result['expired_since_days']
                    })
                elif expiry_result['status'] == 'expiring_soon':
                    expiring_soon.append({
                        'file_id': file_record['id'],
                        'file_path': file_record['file_path'],
                        'file_name': file_record['file_name'],
                        'retention_policy': file_record['retention_policy'],
                        'expires_in_days': expiry_result['expires_in_days']
                    })
            
            logger.info(f"File expiry scan completed: {len(expired_files)} expired, {len(expiring_soon)} expiring soon")
            
            return {
                'scan_time': now.isoformat(),
                'total_files_scanned': len(files_with_policies),
                'expired_files': expired_files,
                'expiring_soon_files': expiring_soon,
                'expired_count': len(expired_files),
                'expiring_soon_count': len(expiring_soon),
                'total_expired_size_bytes': sum(f['size_bytes'] for f in expired_files)
            }
            
        except Exception as e:
            logger.error(f"Error scanning expired files: {e}")
            raise
    
    def purge_expired_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """Purge files that have exceeded their retention period."""
        try:
            # Get expired files
            scan_result = self.scan_expired_files()
            expired_files = scan_result['expired_files']
            
            if not expired_files:
                return {
                    'purge_time': datetime.now(timezone.utc).isoformat(),
                    'dry_run': dry_run,
                    'files_purged': 0,
                    'bytes_freed': 0,
                    'message': 'No expired files found'
                }
            
            purged_files = []
            purge_failures = []
            total_bytes_freed = 0
            
            for file_info in expired_files:
                try:
                    if not dry_run:
                        # Actually delete the file
                        purge_result = self._purge_file(file_info)
                        if purge_result['success']:
                            total_bytes_freed += file_info['size_bytes']
                            purged_files.append(file_info)
                            
                            # Update database record
                            self._mark_file_as_purged(file_info['file_id'])
                        else:
                            purge_failures.append({
                                'file_id': file_info['file_id'],
                                'error': purge_result['error']
                            })
                    else:
                        # Dry run - just add to purged list
                        total_bytes_freed += file_info['size_bytes']
                        purged_files.append(file_info)
                        
                except Exception as e:
                    logger.error(f"Error purging file {file_info['file_id']}: {e}")
                    purge_failures.append({
                        'file_id': file_info['file_id'],
                        'error': str(e)
                    })
            
            # Trigger webhook for purge completion
            if not dry_run and purged_files:
                self.webhook_triggers.files_purged({
                    'files_purged_count': len(purged_files),
                    'bytes_freed': total_bytes_freed,
                    'purge_time': datetime.now(timezone.utc).isoformat(),
                    'failures_count': len(purge_failures)
                })
            
            logger.info(f"File purge completed: {len(purged_files)} files purged, {total_bytes_freed} bytes freed")
            
            return {
                'purge_time': datetime.now(timezone.utc).isoformat(),
                'dry_run': dry_run,
                'files_purged': len(purged_files),
                'bytes_freed': total_bytes_freed,
                'purge_failures': len(purge_failures),
                'purged_files': purged_files[:10],  # Show first 10 for summary
                'failure_details': purge_failures
            }
            
        except Exception as e:
            logger.error(f"Error purging expired files: {e}")
            raise
    
    def check_storage_quotas(self) -> Dict[str, Any]:
        """Check storage quotas for all customers and resellers."""
        try:
            # Get storage usage by customer/reseller
            storage_usage = self._get_storage_usage_by_entity()
            
            quota_violations = []
            quota_warnings = []
            
            for entity in storage_usage:
                quota_check = self._check_entity_quota(entity)
                
                if quota_check['status'] == 'exceeded':
                    quota_violations.append({
                        'entity_type': entity['entity_type'],
                        'entity_id': entity['entity_id'],
                        'entity_name': entity.get('entity_name'),
                        'usage_bytes': entity['usage_bytes'],
                        'quota_bytes': entity['quota_bytes'],
                        'overage_bytes': quota_check['overage_bytes'],
                        'usage_percentage': quota_check['usage_percentage']
                    })
                elif quota_check['status'] == 'warning':
                    quota_warnings.append({
                        'entity_type': entity['entity_type'],
                        'entity_id': entity['entity_id'],
                        'entity_name': entity.get('entity_name'),
                        'usage_bytes': entity['usage_bytes'],
                        'quota_bytes': entity['quota_bytes'],
                        'usage_percentage': quota_check['usage_percentage']
                    })
            
            # Trigger alerts for quota violations
            for violation in quota_violations:
                self.webhook_triggers.storage_quota_exceeded({
                    'entity_type': violation['entity_type'],
                    'entity_id': violation['entity_id'],
                    'usage_bytes': violation['usage_bytes'],
                    'quota_bytes': violation['quota_bytes'],
                    'overage_bytes': violation['overage_bytes'],
                    'alert_time': datetime.now(timezone.utc).isoformat()
                })
            
            logger.info(f"Storage quota check completed: {len(quota_violations)} violations, {len(quota_warnings)} warnings")
            
            return {
                'check_time': datetime.now(timezone.utc).isoformat(),
                'total_entities_checked': len(storage_usage),
                'quota_violations': quota_violations,
                'quota_warnings': quota_warnings,
                'violations_count': len(quota_violations),
                'warnings_count': len(quota_warnings)
            }
            
        except Exception as e:
            logger.error(f"Error checking storage quotas: {e}")
            raise
    
    def get_storage_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get storage usage analytics for a given period."""
        try:
            period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get storage metrics
            analytics = self._calculate_storage_analytics(period_start)
            
            return {
                'period_start': period_start.isoformat(),
                'period_end': datetime.now(timezone.utc).isoformat(),
                'period_days': period_days,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error calculating storage analytics: {e}")
            raise
    
    def set_file_retention_policy(
        self, 
        file_id: int, 
        retention_policy: FileRetentionPolicy
    ) -> Dict[str, Any]:
        """Set retention policy for a specific file."""
        try:
            # Get file record
            file_record = self._get_file_record(file_id)
            if not file_record:
                raise NotFoundError(f"File {file_id} not found")
            
            # Calculate new expiry date
            expiry_date = self._calculate_expiry_date(retention_policy)
            
            # Update file record
            self._update_file_retention_policy(file_id, retention_policy, expiry_date)
            
            logger.info(f"Updated retention policy for file {file_id} to {retention_policy}")
            
            return {
                'file_id': file_id,
                'file_name': file_record['file_name'],
                'old_retention_policy': file_record.get('retention_policy'),
                'new_retention_policy': retention_policy,
                'expiry_date': expiry_date.isoformat() if expiry_date else None,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting file retention policy: {e}")
            raise
    
    def archive_old_files(self, archive_threshold_days: int = 90) -> Dict[str, Any]:
        """Archive files older than the specified threshold."""
        try:
            # Get files eligible for archiving
            archive_candidates = self._get_archive_candidates(archive_threshold_days)
            
            archived_files = []
            archive_failures = []
            total_bytes_archived = 0
            
            for file_record in archive_candidates:
                try:
                    archive_result = self._archive_file(file_record)
                    if archive_result['success']:
                        total_bytes_archived += file_record['size_bytes']
                        archived_files.append({
                            'file_id': file_record['id'],
                            'file_name': file_record['file_name'],
                            'original_path': file_record['file_path'],
                            'archive_path': archive_result['archive_path'],
                            'size_bytes': file_record['size_bytes']
                        })
                        
                        # Update database record
                        self._mark_file_as_archived(file_record['id'], archive_result['archive_path'])
                    else:
                        archive_failures.append({
                            'file_id': file_record['id'],
                            'error': archive_result['error']
                        })
                        
                except Exception as e:
                    logger.error(f"Error archiving file {file_record['id']}: {e}")
                    archive_failures.append({
                        'file_id': file_record['id'],
                        'error': str(e)
                    })
            
            logger.info(f"File archiving completed: {len(archived_files)} files archived, {total_bytes_archived} bytes")
            
            return {
                'archive_time': datetime.now(timezone.utc).isoformat(),
                'archive_threshold_days': archive_threshold_days,
                'files_archived': len(archived_files),
                'bytes_archived': total_bytes_archived,
                'archive_failures': len(archive_failures),
                'archived_files': archived_files[:10],  # Show first 10
                'failure_details': archive_failures
            }
            
        except Exception as e:
            logger.error(f"Error archiving old files: {e}")
            raise
    
    def _get_files_with_retention_policies(self) -> List[Dict[str, Any]]:
        """Get all files that have retention policies."""
        # Placeholder - implement when file repository is available
        # This would query the files table for files with retention_policy set
        return [
            {
                'id': 1,
                'file_name': 'customer_document_1.pdf',
                'file_path': '/storage/documents/customer_document_1.pdf',
                'size_bytes': 1024000,
                'retention_policy': FileRetentionPolicy.SHORT_TERM,
                'created_at': datetime.now(timezone.utc) - timedelta(days=35),
                'entity_type': 'customer',
                'entity_id': 1
            },
            {
                'id': 2,
                'file_name': 'temp_upload.jpg',
                'file_path': '/storage/temp/temp_upload.jpg',
                'size_bytes': 512000,
                'retention_policy': FileRetentionPolicy.TEMPORARY,
                'created_at': datetime.now(timezone.utc) - timedelta(days=10),
                'entity_type': 'customer',
                'entity_id': 2
            }
        ]
    
    def _check_file_expiry(self, file_record: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        """Check if a file has expired or is expiring soon."""
        retention_policy = file_record['retention_policy']
        created_at = file_record['created_at']
        
        if retention_policy == FileRetentionPolicy.PERMANENT:
            return {'status': 'permanent', 'never_expires': True}
        
        retention_days = self.retention_policies[retention_policy]
        expiry_date = created_at + timedelta(days=retention_days)
        
        if now > expiry_date:
            expired_since = now - expiry_date
            return {
                'status': 'expired',
                'expired_since_days': expired_since.days,
                'expiry_date': expiry_date.isoformat()
            }
        elif (expiry_date - now).days <= 7:  # Expiring within 7 days
            expires_in = expiry_date - now
            return {
                'status': 'expiring_soon',
                'expires_in_days': expires_in.days,
                'expiry_date': expiry_date.isoformat()
            }
        else:
            expires_in = expiry_date - now
            return {
                'status': 'active',
                'expires_in_days': expires_in.days,
                'expiry_date': expiry_date.isoformat()
            }
    
    def _purge_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Actually delete a file from storage."""
        try:
            file_path = Path(file_info['file_path'])
            
            if file_path.exists():
                file_path.unlink()  # Delete the file
                return {'success': True}
            else:
                return {'success': False, 'error': 'File not found on disk'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _mark_file_as_purged(self, file_id: int):
        """Mark a file as purged in the database."""
        # Placeholder - implement when file repository is available
        # This would update the file record with purged status and timestamp
        pass
    
    def _get_storage_usage_by_entity(self) -> List[Dict[str, Any]]:
        """Get storage usage aggregated by customer/reseller."""
        # Placeholder - implement when file repository is available
        return [
            {
                'entity_type': 'customer',
                'entity_id': 1,
                'entity_name': 'John Doe',
                'usage_bytes': 52428800,  # 50MB
                'quota_bytes': 104857600,  # 100MB
                'file_count': 25
            },
            {
                'entity_type': 'customer',
                'entity_id': 2,
                'entity_name': 'Jane Smith',
                'usage_bytes': 157286400,  # 150MB
                'quota_bytes': 104857600,   # 100MB (over quota)
                'file_count': 45
            }
        ]
    
    def _check_entity_quota(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an entity has exceeded their storage quota."""
        usage_bytes = entity['usage_bytes']
        quota_bytes = entity['quota_bytes']
        usage_percentage = (usage_bytes / quota_bytes) * 100
        
        if usage_bytes > quota_bytes:
            return {
                'status': 'exceeded',
                'usage_percentage': usage_percentage,
                'overage_bytes': usage_bytes - quota_bytes
            }
        elif usage_percentage >= 80:  # Warning at 80%
            return {
                'status': 'warning',
                'usage_percentage': usage_percentage
            }
        else:
            return {
                'status': 'ok',
                'usage_percentage': usage_percentage
            }
    
    def _calculate_storage_analytics(self, period_start: datetime) -> Dict[str, Any]:
        """Calculate storage analytics for a period."""
        # Placeholder - implement when file repository is available
        return {
            'total_files': 1250,
            'total_size_bytes': 5368709120,  # 5GB
            'files_uploaded': 150,
            'files_deleted': 45,
            'files_archived': 25,
            'average_file_size_bytes': 4294967,
            'storage_growth_bytes': 524288000,  # 500MB growth
            'top_file_types': [
                {'extension': 'pdf', 'count': 450, 'size_bytes': 2147483648},
                {'extension': 'jpg', 'count': 320, 'size_bytes': 1073741824},
                {'extension': 'doc', 'count': 280, 'size_bytes': 1610612736}
            ],
            'retention_policy_distribution': {
                'temporary': 150,
                'short_term': 400,
                'medium_term': 350,
                'long_term': 300,
                'permanent': 50
            }
        }
    
    def _get_file_record(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file record from database."""
        # Placeholder - implement when file repository is available
        return {
            'id': file_id,
            'file_name': 'example.pdf',
            'file_path': '/storage/documents/example.pdf',
            'retention_policy': FileRetentionPolicy.SHORT_TERM
        }
    
    def _calculate_expiry_date(self, retention_policy: FileRetentionPolicy) -> Optional[datetime]:
        """Calculate expiry date based on retention policy."""
        if retention_policy == FileRetentionPolicy.PERMANENT:
            return None
        
        retention_days = self.retention_policies[retention_policy]
        return datetime.now(timezone.utc) + timedelta(days=retention_days)
    
    def _update_file_retention_policy(self, file_id: int, retention_policy: FileRetentionPolicy, expiry_date: Optional[datetime]):
        """Update file retention policy in database."""
        # Placeholder - implement when file repository is available
        pass
    
    def _get_archive_candidates(self, threshold_days: int) -> List[Dict[str, Any]]:
        """Get files eligible for archiving."""
        # Placeholder - implement when file repository is available
        return []
    
    def _archive_file(self, file_record: Dict[str, Any]) -> Dict[str, Any]:
        """Archive a file to long-term storage."""
        try:
            # Mock archiving logic
            original_path = Path(file_record['file_path'])
            archive_path = Path('/storage/archive') / original_path.name
            
            # In real implementation, this would move file to archive storage
            # shutil.move(str(original_path), str(archive_path))
            
            return {
                'success': True,
                'archive_path': str(archive_path)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _mark_file_as_archived(self, file_id: int, archive_path: str):
        """Mark a file as archived in the database."""
        # Placeholder - implement when file repository is available
        pass
