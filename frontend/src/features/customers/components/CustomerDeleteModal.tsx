'use client';

import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
// Button import removed - not used in this component
import { Loader2, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { CustomerUI } from '@/mappers/customers/customerMapper';

interface CustomerDeleteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  customer: CustomerUI | null;
  onConfirm: (customerId: number) => Promise<void>;
  loading?: boolean;
}

export function CustomerDeleteModal({
  open,
  onOpenChange,
  customer,
  onConfirm,
  loading = false,
}: CustomerDeleteModalProps) {
  const { toast } = useToast();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    if (!customer) return;

    try {
      setIsDeleting(true);
      await onConfirm(customer.id);
      toast({
        title: 'Customer Deleted',
        description: `${customer.name} has been successfully deleted.`,
      });
      onOpenChange(false);
    } catch (_error) {
      toast({
        title: 'Error',
        description: 'Failed to delete customer. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  if (!customer) return null;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <AlertDialogTitle>Delete Customer</AlertDialogTitle>
              <AlertDialogDescription className="mt-1">
                Are you sure you want to delete <strong>{customer.name}</strong>?
              </AlertDialogDescription>
            </div>
          </div>
        </AlertDialogHeader>

        <div className="py-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-red-800 mb-2">
              This action cannot be undone
            </h4>
            <ul className="text-sm text-red-700 space-y-1">
              <li>• Customer account will be permanently deleted</li>
              <li>• All associated service history will be removed</li>
              <li>• Billing records will be archived but customer access will be revoked</li>
              <li>• This action is irreversible</li>
            </ul>
          </div>

          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Customer Details</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <div><strong>Email:</strong> {customer.email}</div>
              <div><strong>Phone:</strong> {customer.phone}</div>
              <div><strong>Status:</strong> {customer.status}</div>
              {customer.servicePlan && (
                <div><strong>Service Plan:</strong> {customer.servicePlan}</div>
              )}
              {customer.monthlyFee && (
                <div><strong>Monthly Fee:</strong> ${customer.monthlyFee.toFixed(2)}</div>
              )}
            </div>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting || loading}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isDeleting || loading}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {isDeleting || loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete Customer'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
