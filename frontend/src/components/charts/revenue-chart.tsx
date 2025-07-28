'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Sample data for ISP dashboard
const revenueData = [
  { month: 'Jan', revenue: 45000, customers: 1200 },
  { month: 'Feb', revenue: 52000, customers: 1280 },
  { month: 'Mar', revenue: 48000, customers: 1250 },
  { month: 'Apr', revenue: 61000, customers: 1350 },
  { month: 'May', revenue: 55000, customers: 1320 },
  { month: 'Jun', revenue: 67000, customers: 1420 },
];

const serviceData = [
  { name: 'Internet', value: 65, color: '#0088FE' },
  { name: 'Voice', value: 25, color: '#00C49F' },
  { name: 'Bundle', value: 10, color: '#FFBB28' },
];

interface ChartProps {
  className?: string;
}

export function RevenueLineChart({ className }: ChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={revenueData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip formatter={(value, name) => [`$${value}`, name]} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="revenue" 
            stroke="#8884d8" 
            strokeWidth={2}
            name="Revenue"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CustomerBarChart({ className }: ChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={revenueData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="customers" fill="#82ca9d" name="Customers" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ServicePieChart({ className }: ChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={serviceData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {serviceData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
