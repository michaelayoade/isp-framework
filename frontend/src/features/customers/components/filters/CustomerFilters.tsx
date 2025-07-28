'use client';

import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { CustomerFilters as CustomerFiltersType, CustomerStatus, AccountType } from '../../types';

interface CustomerFiltersProps {
  filters: CustomerFiltersType;
  onFiltersChange: (filters: Partial<CustomerFiltersType>) => void;
}

export function CustomerFilters({ filters, onFiltersChange }: CustomerFiltersProps) {
  const handleClearFilters = () => {
    onFiltersChange({
      search: undefined,
      status: undefined,
      account_type: undefined,
      service_type: undefined,
    });
  };

  const hasActiveFilters = filters.search || filters.status || filters.account_type || filters.service_type;

  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <div className="flex-1">
        <Input
          placeholder="Search customers..."
          value={filters.search || ''}
          onChange={(e) => onFiltersChange({ search: e.target.value || undefined })}
          className="max-w-sm"
        />
      </div>
      
      <div className="flex gap-2">
        <Select
          value={filters.status || 'all'}
          onValueChange={(value) => onFiltersChange({ status: value === 'all' ? undefined : value as CustomerStatus })}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.account_type || 'all'}
          onValueChange={(value) => onFiltersChange({ account_type: value === 'all' ? undefined : value as AccountType })}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Account Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="residential">Residential</SelectItem>
            <SelectItem value="business">Business</SelectItem>
            <SelectItem value="enterprise">Enterprise</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.service_type || 'all'}
          onValueChange={(value) => onFiltersChange({ service_type: value === 'all' ? undefined : value })}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Service Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Services</SelectItem>
            <SelectItem value="internet">Internet</SelectItem>
            <SelectItem value="voice">Voice</SelectItem>
            <SelectItem value="bundle">Bundle</SelectItem>
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button variant="outline" size="sm" onClick={handleClearFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}
