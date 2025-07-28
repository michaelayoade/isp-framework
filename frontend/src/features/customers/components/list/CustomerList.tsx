'use client';

import { useState } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
} from '@tanstack/react-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Eye, Edit, UserX, UserCheck } from 'lucide-react';
import { useSuspendCustomer, useReactivateCustomer } from '../../hooks/useCustomers';
import type { Customer, PaginatedResponse } from '../../types';

interface CustomerListProps {
  data?: PaginatedResponse<Customer>;
  isLoading: boolean;
  onPageChange: (page: number) => void;
}

export function CustomerList({ data, isLoading, onPageChange }: CustomerListProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  
  const suspendCustomer = useSuspendCustomer();
  const reactivateCustomer = useReactivateCustomer();

  const columns: ColumnDef<Customer>[] = [
    {
      accessorKey: 'customer_number',
      header: 'Customer #',
    },
    {
      accessorKey: 'first_name',
      header: 'Name',
      cell: ({ row }) => {
        const customer = row.original;
        return `${customer.first_name} ${customer.last_name}`;
      },
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'phone',
      header: 'Phone',
    },
    {
      accessorKey: 'account_type',
      header: 'Account Type',
      cell: ({ row }) => {
        const type = row.getValue('account_type') as string;
        return (
          <Badge variant={type === 'enterprise' ? 'default' : 'secondary'}>
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        const variant = status === 'active' ? 'default' : 
                      status === 'suspended' ? 'destructive' : 'secondary';
        return (
          <Badge variant={variant}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'services',
      header: 'Services',
      cell: ({ row }) => {
        const services = row.original.services;
        return services?.length || 0;
      },
    },
    {
      accessorKey: 'billing_info.outstanding_balance',
      header: 'Balance',
      cell: ({ row }) => {
        const balance = row.original.billing_info?.outstanding_balance || 0;
        return (
          <span className={balance > 0 ? 'text-red-600' : 'text-green-600'}>
            ${balance.toFixed(2)}
          </span>
        );
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const customer = row.original;
        
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Edit className="mr-2 h-4 w-4" />
                Edit Customer
              </DropdownMenuItem>
              {customer.status === 'active' ? (
                <DropdownMenuItem
                  onClick={() => suspendCustomer.mutate({ id: customer.id })}
                  className="text-red-600"
                >
                  <UserX className="mr-2 h-4 w-4" />
                  Suspend
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() => reactivateCustomer.mutate(customer.id)}
                  className="text-green-600"
                >
                  <UserCheck className="mr-2 h-4 w-4" />
                  Reactivate
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data: data?.data || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted animate-pulse rounded" />
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="h-12 bg-muted animate-pulse rounded" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No customers found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing {((data.page - 1) * data.per_page) + 1} to {Math.min(data.page * data.per_page, data.total)} of {data.total} customers
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(data.page - 1)}
              disabled={data.page <= 1}
            >
              Previous
            </Button>
            <div className="text-sm">
              Page {data.page} of {data.total_pages}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(data.page + 1)}
              disabled={data.page >= data.total_pages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
