import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import Layout from "../components/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, AlertTriangle, CheckCircle, Clock, TrendingUp, Database } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

const Dashboard = ({ setIsAuthenticated }) => {
  const [stats, setStats] = useState(null);
  const [fraudByType, setFraudByType] = useState([]);
  const [fraudByDistrict, setFraudByDistrict] = useState([]);
  const [transactionsTrend, setTransactionsTrend] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, fraudTypeRes, fraudDistrictRes, trendRes] = await Promise.all([
        axios.get(`${API}/analytics/dashboard`),
        axios.get(`${API}/analytics/fraud-by-type`),
        axios.get(`${API}/analytics/fraud-by-district`),
        axios.get(`${API}/analytics/transactions-trend`)
      ]);

      setStats(statsRes.data);
      setFraudByType(fraudTypeRes.data);
      setFraudByDistrict(fraudDistrictRes.data);
      setTransactionsTrend(trendRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = stats ? [
    {
      title: "Total Users",
      value: stats.total_users,
      icon: Users,
      color: "from-blue-500 to-blue-600",
      bgColor: "bg-blue-50",
      testId: "total-users-stat"
    },
    {
      title: "Active Users",
      value: stats.active_users,
      icon: CheckCircle,
      color: "from-green-500 to-green-600",
      bgColor: "bg-green-50",
      testId: "active-users-stat"
    },
    {
      title: "Flagged Users",
      value: stats.flagged_users,
      icon: AlertTriangle,
      color: "from-red-500 to-red-600",
      bgColor: "bg-red-50",
      testId: "flagged-users-stat"
    },
    {
      title: "Pending Alerts",
      value: stats.pending_alerts,
      icon: Clock,
      color: "from-amber-500 to-amber-600",
      bgColor: "bg-amber-50",
      testId: "pending-alerts-stat"
    },
    {
      title: "Confirmed Frauds",
      value: stats.confirmed_frauds,
      icon: AlertTriangle,
      color: "from-purple-500 to-purple-600",
      bgColor: "bg-purple-50",
      testId: "confirmed-frauds-stat"
    },
    {
      title: "Total Transactions",
      value: stats.total_transactions,
      icon: Database,
      color: "from-indigo-500 to-indigo-600",
      bgColor: "bg-indigo-50",
      testId: "total-transactions-stat"
    }
  ] : [];

  if (loading) {
    return (
      <Layout setIsAuthenticated={setIsAuthenticated}>
        <div className="flex items-center justify-center h-96">
          <div className="text-xl text-gray-500">Loading dashboard...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout setIsAuthenticated={setIsAuthenticated}>
      <div className="space-y-6" data-testid="dashboard-container">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
          <p className="text-gray-500 mt-1">Real-time fraud detection monitoring</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow" data-testid={stat.testId}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
                      <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                    </div>
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-lg`}>
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Fraud Types Chart */}
          <Card className="border-0 shadow-md" data-testid="fraud-types-chart">
            <CardHeader>
              <CardTitle className="text-xl">Fraud Cases by Type</CardTitle>
            </CardHeader>
            <CardContent>
              {fraudByType.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={fraudByType}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ type, percent }) => `${type} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {fraudByType.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  No fraud data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Fraud Hotspots Chart */}
          <Card className="border-0 shadow-md" data-testid="fraud-hotspots-chart">
            <CardHeader>
              <CardTitle className="text-xl">Fraud Hotspots by District</CardTitle>
            </CardHeader>
            <CardContent>
              {fraudByDistrict.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={fraudByDistrict}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="district" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  No district data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Transaction Trends */}
        <Card className="border-0 shadow-md" data-testid="transaction-trends-chart">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Transaction Trends (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {transactionsTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={transactionsTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-500">
                No transaction data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Dashboard;
