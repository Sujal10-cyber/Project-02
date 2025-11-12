import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import Layout from "../components/Layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Brain, TrendingUp, MapPin } from "lucide-react";

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

const Analytics = ({ setIsAuthenticated }) => {
  const [fraudByType, setFraudByType] = useState([]);
  const [fraudByDistrict, setFraudByDistrict] = useState([]);
  const [transactionsTrend, setTransactionsTrend] = useState([]);
  const [mlStatus, setMlStatus] = useState({ is_trained: false });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [fraudTypeRes, fraudDistrictRes, trendRes, mlRes] = await Promise.all([
        axios.get(`${API}/analytics/fraud-by-type`),
        axios.get(`${API}/analytics/fraud-by-district`),
        axios.get(`${API}/analytics/transactions-trend`),
        axios.get(`${API}/ml/status`)
      ]);

      setFraudByType(fraudTypeRes.data);
      setFraudByDistrict(fraudDistrictRes.data);
      setTransactionsTrend(trendRes.data);
      setMlStatus(mlRes.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModel = async () => {
    try {
      const response = await axios.post(`${API}/ml/train`);
      if (response.data.success) {
        toast.success("ML model trained successfully");
        fetchAnalytics();
      } else {
        toast.warning(response.data.message);
      }
    } catch (error) {
      toast.error("Failed to train model");
    }
  };

  if (loading) {
    return (
      <Layout setIsAuthenticated={setIsAuthenticated}>
        <div className="flex items-center justify-center h-96">
          <div className="text-xl text-gray-500">Loading analytics...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout setIsAuthenticated={setIsAuthenticated}>
      <div className="space-y-6" data-testid="analytics-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
            <p className="text-gray-500 mt-1">Deep insights into fraud patterns</p>
          </div>
        </div>

        {/* ML Model Status */}
        <Card className="border-0 shadow-md bg-gradient-to-r from-indigo-50 to-purple-50" data-testid="ml-status-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">ML Fraud Detection Model</h3>
                  <p className="text-sm text-gray-600">
                    Status: <span className={`font-medium ${mlStatus.is_trained ? 'text-green-600' : 'text-amber-600'}`}>
                      {mlStatus.is_trained ? 'Trained & Active' : 'Not Trained'}
                    </span>
                  </p>
                  <p className="text-xs text-gray-500">Model Type: {mlStatus.model_type || 'Isolation Forest'}</p>
                </div>
              </div>
              <Button
                onClick={handleTrainModel}
                data-testid="train-model-button"
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
              >
                {mlStatus.is_trained ? 'Retrain Model' : 'Train Model'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Fraud by Type */}
          <Card className="border-0 shadow-md" data-testid="fraud-types-analytics">
            <CardHeader>
              <CardTitle className="text-xl">Fraud Distribution by Type</CardTitle>
            </CardHeader>
            <CardContent>
              {fraudByType.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <PieChart>
                    <Pie
                      data={fraudByType}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ type, percent }) => `${type.slice(0, 15)}... ${(percent * 100).toFixed(0)}%`}
                      outerRadius={110}
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
                <div className="h-[350px] flex items-center justify-center text-gray-500">
                  No fraud data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Fraud Hotspots */}
          <Card className="border-0 shadow-md" data-testid="fraud-hotspots-analytics">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Fraud Hotspots by District
              </CardTitle>
            </CardHeader>
            <CardContent>
              {fraudByDistrict.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={fraudByDistrict}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="district" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#ec4899" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex items-center justify-center text-gray-500">
                  No district data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Transaction Trends */}
        <Card className="border-0 shadow-md" data-testid="transaction-trends-analytics">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Transaction Volume Trends (30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {transactionsTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={transactionsTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#10b981" 
                    strokeWidth={3} 
                    dot={{ r: 5 }} 
                    activeDot={{ r: 7 }}
                    name="Transactions"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[350px] flex items-center justify-center text-gray-500">
                No transaction data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Analytics;
