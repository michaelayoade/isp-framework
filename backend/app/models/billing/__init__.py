"""
Billing System

Comprehensive ISP billing module with advanced features:
- Real-time balance management
- Hybrid prepaid/postpaid billing
- Dunning management
- Payment plans and installments
- Proration capabilities
- Advanced ISP billing features

This modular approach provides:
- Clean separation of concerns
- Easy maintenance and updates
- Independent testing capabilities
- Selective imports for services and APIs
- Scalable architecture
"""

# Import all enumerations
from .enums import (
    BillingType,
    AccountStatus,
    TransactionType,
    TransactionCategory,
    InvoiceStatus,
    PaymentStatus,
    PaymentMethodType,
    DunningStatus,
    PaymentPlanStatus,
    BillingCycleType,
    CreditNoteReason,
    InstallmentStatus,
    DunningActionType,
    EscalationLevel,
    DeliveryStatus
)

# Import account management models
from .accounts import (
    CustomerBillingAccount
)

# Import transaction models
from .transactions import (
    BillingTransaction,
    BalanceHistory,
    TransactionBatch
)

# Import invoice models
from .invoices import (
    Invoice, InvoiceItem, InvoiceTemplate
)

# Import payment models
from .payments import (
    PaymentMethod, Payment, PaymentRefund, PaymentGateway
)

# Import credit note models
from .credit_notes import (
    CreditNote, CreditNoteTemplate, CreditNoteApproval
)

# Import payment plan models
from .payment_plans import (
    PaymentPlan,
    PaymentPlanInstallment,
    PaymentPlanTemplate
)

# Import dunning models
from .dunning import (
    DunningCase,
    DunningAction,
    DunningTemplate,
    DunningRule
)

# Import accounting models
from .accounting import (
    AccountingEntry,
    ChartOfAccounts
)

# Import tax models

# Import billing cycle models
from .billing_cycles import (
    BillingCycle,
    BillingCycleCustomer,
    BillingCycleTemplate,
    BillingCycleJob
)

# Export all models for easy importing
__all__ = [
    # Enumerations
    "BillingType",
    "AccountStatus",
    "TransactionType",
    "TransactionCategory",
    "InvoiceStatus",
    "PaymentStatus",
    "PaymentMethodType",
    "DunningStatus",
    "PaymentPlanStatus",
    "BillingCycleType",
    "CreditNoteReason",
    "InstallmentStatus",
    "DunningActionType",
    "EscalationLevel",
    "DeliveryStatus",
    
    # Account Management
    "CustomerBillingAccount",
    
    # Transactions
    "BillingTransaction",
    "BalanceHistory",
    "TransactionBatch",
    
    # Invoicing
    "Invoice",
    "InvoiceItem",
    "InvoiceTemplate",
    
    # Payments
    "PaymentMethod",
    "Payment",
    "PaymentRefund",
    "PaymentGateway",
    
    # Credit Notes
    "CreditNote",
    "CreditNoteTemplate",
    "CreditNoteApproval",
    
    # Payment Plans
    "PaymentPlan",
    "PaymentPlanInstallment",
    "PaymentPlanTemplate",
    
    # Dunning Management
    "DunningCase",
    "DunningAction",
    "DunningTemplate",
    "DunningRule",
    
    # Billing Cycles
    "BillingCycle",
    "BillingCycleCustomer",
    "BillingCycleTemplate",
    "BillingCycleJob",
    
    # Accounting
    "AccountingEntry",
    "ChartOfAccounts",
]

# Convenience imports removed to avoid F811 redefinition errors
# All models are already imported above in their respective sections

# Module metadata
__version__ = "1.0.0"
__author__ = "ISP Framework Team"
__description__ = "Billing system for ISP operations"

# Module configuration
BILLING_MODULE_CONFIG = {
    "version": __version__,
    "features": [
        "Real-time balance management",
        "Hybrid prepaid/postpaid billing",
        "Automated dunning processes",
        "Flexible payment plans",
        "Comprehensive proration",
        "Multi-gateway payment processing",
        "Advanced credit note management",
        "Automated billing cycles",
        "Transaction audit trails",
        "Comprehensive reporting"
    ],
    "supported_currencies": ["USD", "EUR", "GBP", "NGN", "KES", "GHS"],
    "supported_payment_methods": [
        "cash", "bank_transfer", "credit_card", "debit_card", 
        "mobile_money", "paypal", "stripe", "flutterwave", "paystack"
    ],
    "billing_types": ["prepaid", "postpaid", "hybrid"],
    "billing_cycles": ["monthly", "quarterly", "semi_annual", "annual", "custom"]
}

def get_module_info():
    """Get comprehensive module information"""
    return {
        "name": "Billing System",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "config": BILLING_MODULE_CONFIG,
        "models": {
            "account_management": ["CustomerBillingAccount"],
            "transactions": ["BillingTransaction", "BalanceHistory", "TransactionBatch"],
            "invoicing": ["Invoice", "InvoiceItem", "InvoiceTemplate"],
            "payments": ["PaymentMethod", "Payment", "PaymentRefund", "PaymentGateway"],
            "credit_notes": ["CreditNote", "CreditNoteTemplate", "CreditNoteApproval"],
            "payment_plans": ["PaymentPlan", "PaymentPlanInstallment", "PaymentPlanTemplate"],
            "dunning": ["DunningCase", "DunningAction", "DunningTemplate", "DunningRule"],
            "billing_cycles": ["BillingCycle", "BillingCycleCustomer", "BillingCycleTemplate", "BillingCycleJob"]
        },
        "total_models": len(__all__) - len(BILLING_MODULE_CONFIG["supported_currencies"]) + 4  # Adjust for enums
    }

def validate_billing_configuration():
    """Validate billing system configuration"""
    errors = []
    warnings = []
    
    # Check for required models
    required_models = [
        "CustomerBillingAccount", "BillingTransaction", "BalanceHistory", 
        "Invoice", "InvoiceItem", "PaymentMethod", "Payment", 
        "CreditNote", "PaymentPlan", "DunningCase"
    ]
    
    for model_name in required_models:
        if model_name not in __all__:
            errors.append(f"Required model {model_name} not found in exports")
    
    # Check for circular imports (basic check)
    try:
        from . import accounts, transactions, invoices, payments, credit_notes, payment_plans, dunning, billing_cycles
        warnings.append("All modules imported successfully")
    except ImportError as e:
        errors.append(f"Import error: {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# Initialize module
def initialize_billing_system():
    """Initialize the billing system"""
    validation_result = validate_billing_configuration()
    
    if not validation_result["valid"]:
        raise RuntimeError(f"Billing system validation failed: {validation_result['errors']}")
    
    return {
        "status": "initialized",
        "module_info": get_module_info(),
        "validation": validation_result
    }

# Export utility functions
__all__.extend([
    "get_module_info",
    "validate_billing_configuration", 
    "initialize_billing_system",
    "BillingAccount",  # Convenience alias
    "Invoice",         # Convenience alias
    "InvoiceItem",     # Convenience alias
    "Payment",         # Convenience alias
    "CreditNote"       # Convenience alias
])
