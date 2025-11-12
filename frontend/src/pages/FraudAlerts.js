import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import Layout from "../components/Layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle, XCircle, Eye, TrendingUp } from "lucide-react";

const FraudAlerts = ({ setIsAuthenticated }) => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, statusFilter]);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/fraud-alerts`);
      setAlerts(response.data);
    } catch (error) {
      toast.error("Failed to fetch alerts");
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    if (statusFilter === "all") {
      setFilteredAlerts(alerts);
    } else {
      setFilteredAlerts(alerts.filter(a => a.status === statusFilter));
    }
  };

  const handleUpdateAlert = async (alertId, status) => {
    try {
      await axios.patch(`${API}/fraud-alerts/${alertId}`, { status });
      toast.success(`Alert ${status} successfully`);
      fetchAlerts();
      setShowDetailsDialog(false);
    } catch (error) {
      toast.error("Failed to update alert");
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: { className: "bg-amber-100 text-amber-700" },
      confirmed: { className: "bg-red-100 text-red-700" },
      dismissed: { className: "bg-gray-100 text-gray-700" }
    };
    return <Badge className={variants[status]?.className} data-testid={`alert-status-${status}`}>{status}</Badge>;
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return "text-red-600";
    if (score >= 0.6) return "text-amber-600";
    return "text-gray-600";
  };

  const viewAlertDetails = async (alert) => {
    try {
      // Fetch user details
      const userResponse = await axios.get(`${API}/users/${alert.user_id}`);
      setSelectedAlert({ ...alert, user: userResponse.data });
      setShowDetailsDialog(true);
    } catch (error) {
      toast.error("Failed to fetch alert details");
    }
  };

  return (
    <Layout setIsAuthenticated={setIsAuthenticated}>
      <div className="space-y-6" data-testid="fraud-alerts-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fraud Alerts</h1>
            <p className="text-gray-500 mt-1">Review and manage fraud detection alerts</p>
          </div>
        </div>

        {/* Filter */}
        <Card className="border-0 shadow-md">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700">Filter by Status:</span>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48" data-testid="alert-status-filter">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Alerts</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="confirmed">Confirmed</SelectItem>
                  <SelectItem value="dismissed">Dismissed</SelectItem>
                </SelectContent>
              </Select>
              <div className="ml-auto text-sm text-gray-600">
                Showing {filteredAlerts.length} alerts
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alerts List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading alerts...</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredAlerts.map((alert) => (
              <Card key={alert.id} className="border-0 shadow-md hover:shadow-lg transition-shadow" data-testid={`alert-card-${alert.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                        <h3 className="text-lg font-semibold text-gray-900">{alert.fraud_type}</h3>
                        {getStatusBadge(alert.status)}
                      </div>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <span>Confidence Score:</span>
                          <span className={`font-bold text-base ${getConfidenceColor(alert.confidence_score)}`}>
                            {(alert.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Details:</span> {alert.details.message}
                        </div>
                        <div className="text-xs text-gray-500">
                          Created: {new Date(alert.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => viewAlertDetails(alert)}
                        data-testid={`view-alert-${alert.id}`}
                        className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View
                      </Button>
                      {alert.status === "pending" && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateAlert(alert.id, "confirmed")}
                            data-testid={`confirm-alert-${alert.id}`}
                            className="border-red-200 text-red-700 hover:bg-red-50"
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Confirm
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateAlert(alert.id, "dismissed")}
                            data-testid={`dismiss-alert-${alert.id}`}
                            className="border-gray-200 text-gray-700 hover:bg-gray-50"
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Dismiss
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {filteredAlerts.length === 0 && (
              <Card className="border-0 shadow-md">
                <CardContent className="p-12 text-center text-gray-500">
                  No alerts found
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* Alert Details Dialog */}
      <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
        <DialogContent className="max-w-2xl" data-testid="alert-details-dialog">
          <DialogHeader>
            <DialogTitle>Fraud Alert Details</DialogTitle>
          </DialogHeader>
          {selectedAlert && (
            <div className="space-y-6">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <h3 className="font-semibold text-red-900">{selectedAlert.fraud_type}</h3>
                </div>
                <p className="text-sm text-red-700">{selectedAlert.details.message}</p>
                <div className="mt-3 flex items-center gap-4 text-sm">
                  <span className="text-red-900">
                    Confidence: <strong>{(selectedAlert.confidence_score * 100).toFixed(0)}%</strong>
                  </span>
                  {getStatusBadge(selectedAlert.status)}
                </div>
              </div>

              {selectedAlert.user && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">User Information</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Name:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.name}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Aadhaar ID:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.aadhaar_id}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Address:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.address}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">District:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.district}, {selectedAlert.user.state}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Card Type:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.card_type}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Income:</span>
                      <p className="font-medium text-gray-900">₹{selectedAlert.user.income.toLocaleString()}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Phone:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.phone}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <p className="font-medium text-gray-900">{selectedAlert.user.status}</p>
                    </div>
                  </div>
                </div>
              )}

              {selectedAlert.status === "pending" && (
                <div className="flex gap-3 pt-4 border-t">
                  <Button
                    onClick={() => handleUpdateAlert(selectedAlert.id, "confirmed")}
                    className="flex-1 bg-red-600 hover:bg-red-700"
                    data-testid="confirm-alert-dialog"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Confirm Fraud
                  </Button>
                  <Button
                    onClick={() => handleUpdateAlert(selectedAlert.id, "dismissed")}
                    variant="outline"
                    className="flex-1"
                    data-testid="dismiss-alert-dialog"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Dismiss Alert
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default FraudAlerts;
