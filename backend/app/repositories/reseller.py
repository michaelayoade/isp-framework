"""
Reseller Repository

Database operations for reseller management in single-tenant ISP Framework.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from decimal import Decimal

from app.models.foundation import Reseller
from app.models.customer import Customer
from app.models.billing import Payment
from app.repositories.base import BaseRepository


class ResellerRepository(BaseRepository[Reseller]):
    """Repository for reseller database operations"""
    
    def __init__(self, db: Session):
        super().__init__(Reseller, db)
    
    def get_by_code(self, code: str) -> Optional[Reseller]:
        """Get reseller by unique code"""
        return self.db.query(Reseller).filter(Reseller.code == code).first()
    
    def get_by_email(self, email: str) -> Optional[Reseller]:
        """Get reseller by email"""
        return self.db.query(Reseller).filter(Reseller.email == email).first()
    
    def get_active_resellers(self) -> List[Reseller]:
        """Get all active resellers"""
        return self.db.query(Reseller).filter(Reseller.is_active == True).all()
    
    def get_resellers_by_territory(self, territory: str) -> List[Reseller]:
        """Get resellers by territory"""
        return self.db.query(Reseller).filter(
            and_(
                Reseller.territory == territory,
                Reseller.is_active == True
            )
        ).all()
    
    def get_reseller_with_customer_count(self, reseller_id: int) -> Optional[Dict[str, Any]]:
        """Get reseller with customer count"""
        result = self.db.query(
            Reseller,
            func.count(Customer.id).label('customer_count')
        ).outerjoin(
            Customer, Customer.reseller_id == Reseller.id
        ).filter(
            Reseller.id == reseller_id
        ).group_by(Reseller.id).first()
        
        if result:
            reseller, customer_count = result
            return {
                'reseller': reseller,
                'customer_count': customer_count or 0
            }
        return None
    
    def get_reseller_customers(self, reseller_id: int, limit: int = 50, offset: int = 0) -> List[Customer]:
        """Get customers assigned to a reseller"""
        return self.db.query(Customer).filter(
            Customer.reseller_id == reseller_id
        ).offset(offset).limit(limit).all()
    
    def get_reseller_customer_count(self, reseller_id: int) -> int:
        """Get count of customers assigned to a reseller"""
        return self.db.query(Customer).filter(Customer.reseller_id == reseller_id).count()
    
    def get_reseller_active_customer_count(self, reseller_id: int) -> int:
        """Get count of active customers assigned to a reseller"""
        return self.db.query(Customer).filter(
            and_(
                Customer.reseller_id == reseller_id,
                Customer.status == 'active'
            )
        ).count()
    
    def get_reseller_commission_data(self, reseller_id: int, start_date=None, end_date=None) -> Dict[str, Any]:
        """Get reseller commission data for a period"""
        query = self.db.query(
            func.sum(Payment.amount).label('total_payments'),
            func.count(Payment.id).label('payment_count'),
            func.count(func.distinct(Payment.customer_id)).label('unique_customers')
        ).join(
            Customer, Customer.id == Payment.customer_id
        ).filter(
            Customer.reseller_id == reseller_id
        )
        
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        
        result = query.first()
        
        return {
            'total_payments': result.total_payments or Decimal('0'),
            'payment_count': result.payment_count or 0,
            'unique_customers': result.unique_customers or 0
        }
    
    def get_reseller_stats(self, reseller_id: int) -> Dict[str, Any]:
        """Get comprehensive reseller statistics"""
        reseller = self.get_by_id(reseller_id)
        if not reseller:
            return {}
        
        # Customer counts
        total_customers = self.get_reseller_customer_count(reseller_id)
        active_customers = self.get_reseller_active_customer_count(reseller_id)
        
        # Commission data
        commission_data = self.get_reseller_commission_data(reseller_id)
        total_revenue = commission_data['total_payments']
        commission_amount = total_revenue * (reseller.commission_percentage / 100)
        
        return {
            'reseller_id': reseller_id,
            'reseller_name': reseller.name,
            'customer_count': total_customers,
            'active_customers': active_customers,
            'total_revenue': total_revenue,
            'commission_earned': commission_amount,
            'commission_percentage': reseller.commission_percentage,
            'territory': reseller.territory
        }
    
    def search_resellers(self, query: str, limit: int = 50, offset: int = 0) -> List[Reseller]:
        """Search resellers by name, code, or email"""
        search_filter = f"%{query}%"
        return self.db.query(Reseller).filter(
            and_(
                Reseller.is_active == True,
                (
                    Reseller.name.ilike(search_filter) |
                    Reseller.code.ilike(search_filter) |
                    Reseller.email.ilike(search_filter)
                )
            )
        ).offset(offset).limit(limit).all()
    
    def get_resellers_with_stats(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get resellers with customer count and commission stats"""
        resellers = self.get_all(limit=limit, offset=offset)
        results = []
        
        for reseller in resellers:
            stats = self.get_reseller_stats(reseller.id)
            results.append({
                'reseller': reseller,
                'stats': stats
            })
        
        return results
    
    def check_customer_limit(self, reseller_id: int) -> bool:
        """Check if reseller has reached customer limit"""
        reseller = self.get_by_id(reseller_id)
        if not reseller or not reseller.customer_limit:
            return True  # No limit set
        
        current_count = self.get_reseller_customer_count(reseller_id)
        return current_count < reseller.customer_limit
    
    def assign_customer_to_reseller(self, customer_id: int, reseller_id: int) -> bool:
        """Assign a customer to a reseller"""
        # Check if reseller exists and is active
        reseller = self.get_by_id(reseller_id)
        if not reseller or not reseller.is_active:
            return False
        
        # Check customer limit
        if not self.check_customer_limit(reseller_id):
            return False
        
        # Update customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.reseller_id = reseller_id
            self.db.commit()
            return True
        
        return False
    
    def unassign_customer_from_reseller(self, customer_id: int) -> bool:
        """Remove customer assignment from reseller"""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.reseller_id = None
            self.db.commit()
            return True
        return False
