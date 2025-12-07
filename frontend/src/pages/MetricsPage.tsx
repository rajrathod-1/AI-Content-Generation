import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import { ApiService, MetricsResponse } from '../services/api';
import toast from 'react-hot-toast';

const MetricsPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
    // Set up interval to refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await ApiService.getMetrics();
      setMetrics(data);
    } catch (err) {
      setError('Failed to fetch metrics. Make sure the backend service is running.');
      toast.error('Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  const successRate = metrics ? 
    (metrics.successful_requests / Math.max(metrics.total_requests, 1)) * 100 : 0;

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
  }> = ({ title, value, icon, color, subtitle }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      viewport={{ once: true }}
      className="card"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Metrics</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchMetrics}
            className="btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-2">System Metrics</h1>
          <p className="text-gray-600">Real-time performance monitoring for the RAG system</p>
          <div className="flex items-center mt-2 text-sm text-gray-500">
            <ClockIcon className="h-4 w-4 mr-1" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
            <button
              onClick={fetchMetrics}
              className="ml-4 text-blue-600 hover:text-blue-800 font-medium"
            >
              Refresh
            </button>
          </div>
        </motion.div>

        {/* Main Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Requests"
            value={metrics?.total_requests.toLocaleString() || '0'}
            icon={<ChartBarIcon className="h-6 w-6 text-blue-600" />}
            color="text-blue-600"
            subtitle="All-time requests"
          />
          
          <StatCard
            title="Success Rate"
            value={`${successRate.toFixed(1)}%`}
            icon={<CheckCircleIcon className="h-6 w-6 text-green-600" />}
            color="text-green-600"
            subtitle={`${metrics?.successful_requests || 0} successful`}
          />
          
          <StatCard
            title="Failed Requests"
            value={metrics?.failed_requests.toLocaleString() || '0'}
            icon={<XCircleIcon className="h-6 w-6 text-red-600" />}
            color="text-red-600"
            subtitle="Error responses"
          />
          
          <StatCard
            title="Avg Response Time"
            value={`${metrics?.average_response_time?.toFixed(0) || 0}ms`}
            icon={<ArrowTrendingUpIcon className="h-6 w-6 text-purple-600" />}
            color="text-purple-600"
            subtitle="Performance metric"
          />
        </div>

        {/* Endpoint Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="card mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Requests by Endpoint</h2>
          <div className="space-y-4">
            {metrics?.requests_by_endpoint && Object.entries(metrics.requests_by_endpoint).map(([endpoint, count]) => {
              const percentage = (count / Math.max(metrics.total_requests, 1)) * 100;
              return (
                <div key={endpoint} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">{endpoint}</span>
                    <span className="text-sm text-gray-600">{count} requests ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${percentage}%` }}
                      transition={{ duration: 1, delay: 0.2 }}
                      viewport={{ once: true }}
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${percentage}%` }}
                    ></motion.div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* System Health */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="card"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 relative">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    className="text-gray-200"
                  />
                  <motion.circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    strokeLinecap="round"
                    className="text-blue-600"
                    initial={{ strokeDasharray: "0 175.93" }}
                    whileInView={{ 
                      strokeDasharray: `${(metrics?.system_health?.cpu_usage || 0) * 1.76} 175.93` 
                    }}
                    transition={{ duration: 1, delay: 0.5 }}
                    viewport={{ once: true }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-semibold text-gray-900">
                    {metrics?.system_health?.cpu_usage?.toFixed(1) || 0}%
                  </span>
                </div>
              </div>
              <p className="text-sm font-medium text-gray-700">CPU Usage</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 relative">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    className="text-gray-200"
                  />
                  <motion.circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    strokeLinecap="round"
                    className="text-green-600"
                    initial={{ strokeDasharray: "0 175.93" }}
                    whileInView={{ 
                      strokeDasharray: `${(metrics?.system_health?.memory_usage || 0) * 1.76} 175.93` 
                    }}
                    transition={{ duration: 1, delay: 0.7 }}
                    viewport={{ once: true }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-semibold text-gray-900">
                    {metrics?.system_health?.memory_usage?.toFixed(1) || 0}%
                  </span>
                </div>
              </div>
              <p className="text-sm font-medium text-gray-700">Memory Usage</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 relative">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    className="text-gray-200"
                  />
                  <motion.circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    strokeLinecap="round"
                    className="text-purple-600"
                    initial={{ strokeDasharray: "0 175.93" }}
                    whileInView={{ 
                      strokeDasharray: `${(metrics?.system_health?.disk_usage || 0) * 1.76} 175.93` 
                    }}
                    transition={{ duration: 1, delay: 0.9 }}
                    viewport={{ once: true }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-semibold text-gray-900">
                    {metrics?.system_health?.disk_usage?.toFixed(1) || 0}%
                  </span>
                </div>
              </div>
              <p className="text-sm font-medium text-gray-700">Disk Usage</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default MetricsPage;