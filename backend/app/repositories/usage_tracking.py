"""
Usage Tracking Repository

Repository layer for service usage tracking including:
- Service usage data collection and storage
- Usage analytics and reporting
- Performance metrics tracking
- Cost calculation and billing integration
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.orm import Session, joinedload

from app.models.services.management import ServiceUsageTracking
from app.repositories.base import BaseRepository


class UsageRepository(BaseRepository[ServiceUsageTracking]):
    """Repository for service usage tracking."""

    def __init__(self, db: Session):
        super().__init__(ServiceUsageTracking, db)

    def record_usage(
        self,
        customer_service_id: int,
        tracking_date: datetime,
        period_type: str,
        bytes_downloaded: int = 0,
        bytes_uploaded: int = 0,
        session_count: int = 0,
        session_duration_minutes: int = 0,
        peak_download_speed_kbps: Optional[int] = None,
        peak_upload_speed_kbps: Optional[int] = None,
        average_latency_ms: Optional[Decimal] = None,
        incoming_calls: int = 0,
        outgoing_calls: int = 0,
        total_call_minutes: int = 0,
        missed_calls: int = 0,
        voicemail_messages: int = 0,
        uptime_minutes: int = 0,
        downtime_minutes: int = 0,
        packet_loss_percent: Optional[Decimal] = None,
        jitter_ms: Optional[Decimal] = None,
        usage_charges: Decimal = Decimal('0'),
        overage_charges: Decimal = Decimal('0')
    ) -> ServiceUsageTracking:
        """Record usage data for a service."""
        usage_record = ServiceUsageTracking(
            customer_service_id=customer_service_id,
            tracking_date=tracking_date,
            period_type=period_type,
            bytes_downloaded=bytes_downloaded,
            bytes_uploaded=bytes_uploaded,
            session_count=session_count,
            session_duration_minutes=session_duration_minutes,
            peak_download_speed_kbps=peak_download_speed_kbps,
            peak_upload_speed_kbps=peak_upload_speed_kbps,
            average_latency_ms=average_latency_ms,
            incoming_calls=incoming_calls,
            outgoing_calls=outgoing_calls,
            total_call_minutes=total_call_minutes,
            missed_calls=missed_calls,
            voicemail_messages=voicemail_messages,
            uptime_minutes=uptime_minutes,
            downtime_minutes=downtime_minutes,
            packet_loss_percent=packet_loss_percent,
            jitter_ms=jitter_ms,
            usage_charges=usage_charges,
            overage_charges=overage_charges
        )
        self.db.add(usage_record)
        self.db.commit()
        self.db.refresh(usage_record)
        return usage_record

    def get_usage_by_service(
        self,
        customer_service_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period_type: Optional[str] = None
    ) -> List[ServiceUsageTracking]:
        """Get usage records for a specific service."""
        query = self.db.query(ServiceUsageTracking).filter(
            ServiceUsageTracking.customer_service_id == customer_service_id
        )

        if start_date:
            query = query.filter(ServiceUsageTracking.tracking_date >= start_date)
        if end_date:
            query = query.filter(ServiceUsageTracking.tracking_date <= end_date)
        if period_type:
            query = query.filter(ServiceUsageTracking.period_type == period_type)

        return query.order_by(desc(ServiceUsageTracking.tracking_date)).all()

    def get_usage_summary(
        self,
        customer_service_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage summary for a service within date range."""
        query = self.db.query(ServiceUsageTracking).filter(
            and_(
                ServiceUsageTracking.customer_service_id == customer_service_id,
                ServiceUsageTracking.tracking_date >= start_date,
                ServiceUsageTracking.tracking_date <= end_date
            )
        )

        # Aggregate data
        result = query.with_entities(
            func.sum(ServiceUsageTracking.bytes_downloaded).label('total_downloaded'),
            func.sum(ServiceUsageTracking.bytes_uploaded).label('total_uploaded'),
            func.sum(ServiceUsageTracking.session_count).label('total_sessions'),
            func.sum(ServiceUsageTracking.session_duration_minutes).label('total_session_minutes'),
            func.max(ServiceUsageTracking.peak_download_speed_kbps).label('max_download_speed'),
            func.max(ServiceUsageTracking.peak_upload_speed_kbps).label('max_upload_speed'),
            func.avg(ServiceUsageTracking.average_latency_ms).label('avg_latency'),
            func.sum(ServiceUsageTracking.incoming_calls).label('total_incoming_calls'),
            func.sum(ServiceUsageTracking.outgoing_calls).label('total_outgoing_calls'),
            func.sum(ServiceUsageTracking.total_call_minutes).label('total_call_minutes'),
            func.sum(ServiceUsageTracking.uptime_minutes).label('total_uptime'),
            func.sum(ServiceUsageTracking.downtime_minutes).label('total_downtime'),
            func.avg(ServiceUsageTracking.packet_loss_percent).label('avg_packet_loss'),
            func.avg(ServiceUsageTracking.jitter_ms).label('avg_jitter'),
            func.sum(ServiceUsageTracking.usage_charges).label('total_usage_charges'),
            func.sum(ServiceUsageTracking.overage_charges).label('total_overage_charges'),
            func.count(ServiceUsageTracking.id).label('record_count')
        ).first()

        if not result or result.record_count == 0:
            return {
                "total_downloaded_bytes": 0,
                "total_uploaded_bytes": 0,
                "total_data_gb": 0,
                "total_sessions": 0,
                "total_session_minutes": 0,
                "max_download_speed_kbps": 0,
                "max_upload_speed_kbps": 0,
                "avg_latency_ms": 0,
                "total_calls": 0,
                "total_call_minutes": 0,
                "uptime_percentage": 0,
                "avg_packet_loss_percent": 0,
                "avg_jitter_ms": 0,
                "total_charges": 0,
                "record_count": 0
            }

        total_downloaded = int(result.total_downloaded or 0)
        total_uploaded = int(result.total_uploaded or 0)
        total_data_gb = (total_downloaded + total_uploaded) / (1024 ** 3)
        total_uptime = int(result.total_uptime or 0)
        total_downtime = int(result.total_downtime or 0)
        total_time = total_uptime + total_downtime
        uptime_percentage = (total_uptime / total_time * 100) if total_time > 0 else 0

        return {
            "total_downloaded_bytes": total_downloaded,
            "total_uploaded_bytes": total_uploaded,
            "total_data_gb": round(total_data_gb, 2),
            "total_sessions": int(result.total_sessions or 0),
            "total_session_minutes": int(result.total_session_minutes or 0),
            "max_download_speed_kbps": int(result.max_download_speed or 0),
            "max_upload_speed_kbps": int(result.max_upload_speed or 0),
            "avg_latency_ms": float(result.avg_latency or 0),
            "total_calls": int((result.total_incoming_calls or 0) + (result.total_outgoing_calls or 0)),
            "total_call_minutes": int(result.total_call_minutes or 0),
            "uptime_percentage": round(uptime_percentage, 2),
            "avg_packet_loss_percent": float(result.avg_packet_loss or 0),
            "avg_jitter_ms": float(result.avg_jitter or 0),
            "total_charges": float((result.total_usage_charges or 0) + (result.total_overage_charges or 0)),
            "record_count": int(result.record_count)
        }

    def get_usage_trends(
        self,
        customer_service_id: int,
        period_type: str = "daily",
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get usage trends over time."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        query = self.db.query(ServiceUsageTracking).filter(
            and_(
                ServiceUsageTracking.customer_service_id == customer_service_id,
                ServiceUsageTracking.period_type == period_type,
                ServiceUsageTracking.tracking_date >= start_date,
                ServiceUsageTracking.tracking_date <= end_date
            )
        ).order_by(asc(ServiceUsageTracking.tracking_date))

        records = query.all()
        trends = []

        for record in records:
            total_data_gb = (int(record.bytes_downloaded or 0) + int(record.bytes_uploaded or 0)) / (1024 ** 3)
            trends.append({
                "date": record.tracking_date.strftime("%Y-%m-%d"),
                "data_usage_gb": round(total_data_gb, 2),
                "sessions": record.session_count or 0,
                "session_minutes": record.session_duration_minutes or 0,
                "calls": (record.incoming_calls or 0) + (record.outgoing_calls or 0),
                "call_minutes": record.total_call_minutes or 0,
                "uptime_minutes": record.uptime_minutes or 0,
                "downtime_minutes": record.downtime_minutes or 0,
                "charges": float((record.usage_charges or 0) + (record.overage_charges or 0))
            })

        return trends

    def get_top_usage_services(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
        metric: str = "data"  # data, sessions, calls, charges
    ) -> List[Dict[str, Any]]:
        """Get top services by usage metric."""
        if metric == "data":
            order_field = func.sum(ServiceUsageTracking.bytes_downloaded + ServiceUsageTracking.bytes_uploaded)
        elif metric == "sessions":
            order_field = func.sum(ServiceUsageTracking.session_count)
        elif metric == "calls":
            order_field = func.sum(ServiceUsageTracking.incoming_calls + ServiceUsageTracking.outgoing_calls)
        elif metric == "charges":
            order_field = func.sum(ServiceUsageTracking.usage_charges + ServiceUsageTracking.overage_charges)
        else:
            raise ValueError("Metric must be one of: data, sessions, calls, charges")

        query = self.db.query(
            ServiceUsageTracking.customer_service_id,
            func.sum(ServiceUsageTracking.bytes_downloaded + ServiceUsageTracking.bytes_uploaded).label('total_bytes'),
            func.sum(ServiceUsageTracking.session_count).label('total_sessions'),
            func.sum(ServiceUsageTracking.incoming_calls + ServiceUsageTracking.outgoing_calls).label('total_calls'),
            func.sum(ServiceUsageTracking.usage_charges + ServiceUsageTracking.overage_charges).label('total_charges')
        ).filter(
            and_(
                ServiceUsageTracking.tracking_date >= start_date,
                ServiceUsageTracking.tracking_date <= end_date
            )
        ).group_by(
            ServiceUsageTracking.customer_service_id
        ).order_by(
            desc(order_field)
        ).limit(limit)

        results = query.all()
        top_services = []

        for result in results:
            total_data_gb = int(result.total_bytes or 0) / (1024 ** 3)
            top_services.append({
                "customer_service_id": result.customer_service_id,
                "total_data_gb": round(total_data_gb, 2),
                "total_sessions": int(result.total_sessions or 0),
                "total_calls": int(result.total_calls or 0),
                "total_charges": float(result.total_charges or 0)
            })

        return top_services

    def get_usage_alerts(
        self,
        customer_service_id: Optional[int] = None,
        threshold_gb: Optional[float] = None,
        threshold_charges: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get services that exceed usage thresholds."""
        # Get current month usage
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = self.db.query(
            ServiceUsageTracking.customer_service_id,
            func.sum(ServiceUsageTracking.bytes_downloaded + ServiceUsageTracking.bytes_uploaded).label('total_bytes'),
            func.sum(ServiceUsageTracking.usage_charges + ServiceUsageTracking.overage_charges).label('total_charges')
        ).filter(
            ServiceUsageTracking.tracking_date >= month_start
        )

        if customer_service_id:
            query = query.filter(ServiceUsageTracking.customer_service_id == customer_service_id)

        query = query.group_by(ServiceUsageTracking.customer_service_id)
        results = query.all()

        alerts = []
        for result in results:
            total_data_gb = int(result.total_bytes or 0) / (1024 ** 3)
            total_charges = float(result.total_charges or 0)

            alert_reasons = []
            if threshold_gb and total_data_gb > threshold_gb:
                alert_reasons.append(f"Data usage ({total_data_gb:.2f} GB) exceeds threshold ({threshold_gb} GB)")
            if threshold_charges and total_charges > threshold_charges:
                alert_reasons.append(f"Charges (${total_charges:.2f}) exceed threshold (${threshold_charges:.2f})")

            if alert_reasons:
                alerts.append({
                    "customer_service_id": result.customer_service_id,
                    "total_data_gb": round(total_data_gb, 2),
                    "total_charges": total_charges,
                    "alert_reasons": alert_reasons
                })

        return alerts

    def aggregate_usage_by_period(
        self,
        customer_service_id: int,
        period: str = "month",  # day, week, month, year
        count: int = 12
    ) -> List[Dict[str, Any]]:
        """Aggregate usage data by time period."""
        if period == "day":
            date_format = "%Y-%m-%d"
            date_trunc = "day"
        elif period == "week":
            date_format = "%Y-%W"
            date_trunc = "week"
        elif period == "month":
            date_format = "%Y-%m"
            date_trunc = "month"
        elif period == "year":
            date_format = "%Y"
            date_trunc = "year"
        else:
            raise ValueError("Period must be 'day', 'week', 'month', or 'year'")

        # Use database-specific date truncation
        results = self.db.query(
            func.date_trunc(date_trunc, ServiceUsageTracking.tracking_date).label("period"),
            func.sum(ServiceUsageTracking.bytes_downloaded + ServiceUsageTracking.bytes_uploaded).label("total_bytes"),
            func.sum(ServiceUsageTracking.session_count).label("total_sessions"),
            func.sum(ServiceUsageTracking.incoming_calls + ServiceUsageTracking.outgoing_calls).label("total_calls"),
            func.sum(ServiceUsageTracking.usage_charges + ServiceUsageTracking.overage_charges).label("total_charges"),
            func.avg(ServiceUsageTracking.average_latency_ms).label("avg_latency"),
            func.avg(ServiceUsageTracking.packet_loss_percent).label("avg_packet_loss")
        ).filter(
            ServiceUsageTracking.customer_service_id == customer_service_id
        ).group_by(
            func.date_trunc(date_trunc, ServiceUsageTracking.tracking_date)
        ).order_by(
            desc(func.date_trunc(date_trunc, ServiceUsageTracking.tracking_date))
        ).limit(count).all()

        aggregated = []
        for result in results:
            total_data_gb = int(result.total_bytes or 0) / (1024 ** 3)
            aggregated.append({
                "period": result.period.strftime(date_format),
                "total_data_gb": round(total_data_gb, 2),
                "total_sessions": int(result.total_sessions or 0),
                "total_calls": int(result.total_calls or 0),
                "total_charges": float(result.total_charges or 0),
                "avg_latency_ms": float(result.avg_latency or 0),
                "avg_packet_loss_percent": float(result.avg_packet_loss or 0)
            })

        return aggregated

    def cleanup_old_usage_data(self, days_to_keep: int = 365) -> int:
        """Clean up old usage tracking data."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(ServiceUsageTracking).filter(
            ServiceUsageTracking.tracking_date < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted_count

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get overall usage statistics."""
        stats = {}

        # Total records
        stats["total_records"] = self.db.query(ServiceUsageTracking).count()

        # Records by period type
        period_counts = self.db.query(
            ServiceUsageTracking.period_type,
            func.count(ServiceUsageTracking.id)
        ).group_by(ServiceUsageTracking.period_type).all()

        stats["by_period_type"] = {period: count for period, count in period_counts}

        # Date range
        date_range = self.db.query(
            func.min(ServiceUsageTracking.tracking_date),
            func.max(ServiceUsageTracking.tracking_date)
        ).first()

        stats["date_range"] = {
            "earliest": date_range[0].isoformat() if date_range[0] else None,
            "latest": date_range[1].isoformat() if date_range[1] else None
        }

        # Total data processed
        total_data = self.db.query(
            func.sum(ServiceUsageTracking.bytes_downloaded + ServiceUsageTracking.bytes_uploaded)
        ).scalar()

        stats["total_data_gb"] = round((int(total_data or 0) / (1024 ** 3)), 2)

        return stats
