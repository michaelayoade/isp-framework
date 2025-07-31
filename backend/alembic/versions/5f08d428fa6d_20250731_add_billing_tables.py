"""20250731_add_billing_tables

Revision ID: 5f08d428fa6d
Revises: 20250731_squashed_baseline
Create Date: 2025-07-31 15:01:21.509313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f08d428fa6d'
down_revision: Union[str, None] = '20250731_squashed_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing billing tables to resolve SQLAlchemy relationship issues"""
    
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('subtotal', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('tax_amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers_extended.id'], ondelete='CASCADE')
    )
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_number'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers_extended.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL')
    )
    
    # Create credit_notes table
    op.create_table(
        'credit_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credit_note_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('reason', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credit_note_number'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers_extended.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL')
    )
    
    # Create accounting_entries table
    op.create_table(
        'accounting_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_number', sa.String(length=50), nullable=False),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('account_code', sa.String(length=20), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('debit_amount', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('credit_amount', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('credit_note_id', sa.Integer(), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_number'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['credit_note_id'], ['credit_notes.id'], ondelete='SET NULL')
    )
    
    # Create indexes for performance
    op.create_index('idx_invoices_customer_id', 'invoices', ['customer_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    op.create_index('idx_invoices_issue_date', 'invoices', ['issue_date'])
    
    op.create_index('idx_payments_customer_id', 'payments', ['customer_id'])
    op.create_index('idx_payments_invoice_id', 'payments', ['invoice_id'])
    op.create_index('idx_payments_payment_date', 'payments', ['payment_date'])
    
    op.create_index('idx_credit_notes_customer_id', 'credit_notes', ['customer_id'])
    op.create_index('idx_credit_notes_invoice_id', 'credit_notes', ['invoice_id'])
    
    op.create_index('idx_accounting_entries_account_code', 'accounting_entries', ['account_code'])
    op.create_index('idx_accounting_entries_entry_date', 'accounting_entries', ['entry_date'])


def downgrade() -> None:
    """Drop billing tables"""
    op.drop_table('accounting_entries')
    op.drop_table('credit_notes')
    op.drop_table('payments')
    op.drop_table('invoices')
