'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppLayout } from '@/components/ui/layout/app-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search, Plus, Filter, Download, Users, MapPin, Phone, Mail, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { customerService, type Customer } from '@/features/customers/services/customer-service';

const columnHelper = createColumnHelper<Customer>();

export default function CustomersPage() {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  });

  // Fetch customers data
  const { data: customersData, isLoading } = useQuery({
    queryKey: ['customers', pagination.pageIndex + 1, pagination.pageSize, globalFilter],
    queryFn: () => customerService.getCustomers({
      page: pagination.pageIndex + 1,
      per_page: pagination.pageSize,
      search: globalFilter || undefined,
    }),
  });

  const columns = useMemo(
    () => [
      columnHelper.accessor('id', {
        header: 'ID',
        cell: (info) => (
          <span className="font-mono text-sm">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('first_name', {
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 p-0 font-medium"
          >
            Name
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        ),
        cell: (info) => (
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-green-600" />
            <span className="font-medium">{info.row.original.first_name} {info.row.original.last_name}</span>
          </div>
        ),
      }),
      columnHelper.accessor('email', {
        header: 'Email',
        cell: (info) => (
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">{info.getValue()}</span>
          </div>
        ),
      }),
      columnHelper.accessor('phone', {
        header: 'Phone',
        cell: (info) => (
          <div className="flex items-center gap-2">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">{info.getValue()}</span>
          </div>
        ),
      }),
      columnHelper.accessor('billing_address', {
        header: 'Address',
        cell: (info) => {
          const address = info.getValue();
          const addressStr = `${address.street}, ${address.city}, ${address.state}`;
          return (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm truncate max-w-[200px]">{addressStr}</span>
            </div>
          );
        },
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => {
          const status = info.getValue();
          return (
            <Badge
              variant={status === 'active' ? 'default' : status === 'suspended' ? 'destructive' : 'secondary'}
              className={status === 'active' ? 'bg-green-100 text-green-800 hover:bg-green-200' : ''}
            >
              {status}
            </Badge>
          );
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: () => (
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-green-600 hover:text-green-700">
              Edit
            </Button>
            <Button variant="ghost" size="sm">
              View
            </Button>
          </div>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data: customersData?.data || [],
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    manualPagination: true,
    pageCount: customersData ? Math.ceil(customersData.total / pagination.pageSize) : -1,
    state: {
      sorting,
      columnFilters,
      globalFilter,
      pagination,
    },
  });

  return (
    <ProtectedRoute requiredRole="admin">
      <AppLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Customers</h1>
              <p className="text-muted-foreground">
                Manage customer accounts and services
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button size="sm" className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />
                Add Customer
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium leading-none">Total Customers</p>
                    <p className="text-2xl font-bold">{customersData?.total || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Badge className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium leading-none">Active</p>
                    <p className="text-2xl font-bold text-green-600">1,234</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Badge className="h-4 w-4 text-red-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium leading-none">Suspended</p>
                    <p className="text-2xl font-bold text-red-600">23</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Badge className="h-4 w-4 text-gray-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium leading-none">Inactive</p>
                    <p className="text-2xl font-bold text-gray-600">45</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters and Search */}
          <Card>
            <CardHeader>
              <CardTitle>Customer List</CardTitle>
              <CardDescription>
                Search and filter customers by various criteria
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search customers..."
                    value={globalFilter ?? ''}
                    onChange={(event) => setGlobalFilter(String(event.target.value))}
                    className="pl-8"
                  />
                </div>
                <Select>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  More Filters
                </Button>
              </div>

              {/* Table */}
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableRow>
                        <TableCell colSpan={columns.length} className="h-24 text-center">
                          Loading customers...
                        </TableCell>
                      </TableRow>
                    ) : table.getRowModel().rows?.length ? (
                      table.getRowModel().rows.map((row) => (
                        <TableRow
                          key={row.id}
                          data-state={row.getIsSelected() && 'selected'}
                        >
                          {row.getVisibleCells().map((cell) => (
                            <TableCell key={cell.id}>
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
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
              <div className="flex items-center justify-between space-x-2 py-4">
                <div className="text-sm text-muted-foreground">
                  Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
                  {Math.min(
                    (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                    customersData?.total || 0
                  )}{' '}
                  of {customersData?.total || 0} customers
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
