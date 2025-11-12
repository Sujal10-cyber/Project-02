import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import Layout from "../components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Search, UserPlus, Shield, Ban, CheckCircle, AlertTriangle, Eye, Fingerprint } from "lucide-react";

const Users = ({ setIsAuthenticated }) => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedUser, setSelectedUser] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [newUser, setNewUser] = useState({
    aadhaar_id: "",
    name: "",
    address: "",
    district: "",
    state: "",
    family_size: 1,
    income: 0,
    card_type: "BPL",
    phone: ""
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [users, searchTerm, statusFilter]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error("Failed to fetch users");
    } finally {
      setLoading(false);
    }
  };

  const filterUsers = () => {
    let filtered = users;

    if (statusFilter !== "all") {
      filtered = filtered.filter(u => u.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(u => 
        u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.aadhaar_id.includes(searchTerm)
      );
    }

    setFilteredUsers(filtered);
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/users`, newUser);
      toast.success("User added successfully");
      setShowAddDialog(false);
      fetchUsers();
      setNewUser({
        aadhaar_id: "",
        name: "",
        address: "",
        district: "",
        state: "",
        family_size: 1,
        income: 0,
        card_type: "BPL",
        phone: ""
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add user");
    }
  };

  const handleUpdateStatus = async (userId, status) => {
    try {
      await axios.patch(`${API}/users/${userId}/status?status=${status}`);
      toast.success(`User ${status} successfully`);
      fetchUsers();
    } catch (error) {
      toast.error("Failed to update user status");
    }
  };

  const handleVerifyAadhaar = async (userId) => {
    try {
      const response = await axios.post(`${API}/users/${userId}/verify`);
      toast.success(response.data.message);
      fetchUsers();
    } catch (error) {
      toast.error("Verification failed");
    }
  };

  const handleScanForFraud = async (userId) => {
    try {
      const response = await axios.post(`${API}/fraud-alerts/scan/${userId}`);
      toast.info(response.data.message);
    } catch (error) {
      toast.error("Fraud scan failed");
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: { variant: "default", className: "bg-green-100 text-green-700 hover:bg-green-100" },
      suspended: { variant: "secondary", className: "bg-gray-100 text-gray-700 hover:bg-gray-100" },
      flagged: { variant: "destructive", className: "bg-red-100 text-red-700 hover:bg-red-100" }
    };
    return <Badge {...variants[status]} data-testid={`status-badge-${status}`}>{status}</Badge>;
  };

  const getVerificationBadge = (status) => {
    const variants = {
      verified: { className: "bg-green-100 text-green-700" },
      pending: { className: "bg-amber-100 text-amber-700" },
      rejected: { className: "bg-red-100 text-red-700" }
    };
    return <Badge className={variants[status]?.className} data-testid={`verification-badge-${status}`}>{status}</Badge>;
  };

  return (
    <Layout setIsAuthenticated={setIsAuthenticated}>
      <div className="space-y-6" data-testid="users-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
            <p className="text-gray-500 mt-1">Manage ration card holders</p>
          </div>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="bg-indigo-600 hover:bg-indigo-700" data-testid="add-user-button">
                <UserPlus className="w-4 h-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Add New User</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddUser} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Aadhaar ID *</Label>
                    <Input
                      data-testid="aadhaar-input"
                      value={newUser.aadhaar_id}
                      onChange={(e) => setNewUser({ ...newUser, aadhaar_id: e.target.value })}
                      placeholder="XXXX-XXXX-XXXX"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Full Name *</Label>
                    <Input
                      data-testid="name-input"
                      value={newUser.name}
                      onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2 col-span-2">
                    <Label>Address *</Label>
                    <Input
                      data-testid="address-input"
                      value={newUser.address}
                      onChange={(e) => setNewUser({ ...newUser, address: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>District *</Label>
                    <Input
                      data-testid="district-input"
                      value={newUser.district}
                      onChange={(e) => setNewUser({ ...newUser, district: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>State *</Label>
                    <Input
                      data-testid="state-input"
                      value={newUser.state}
                      onChange={(e) => setNewUser({ ...newUser, state: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Family Size *</Label>
                    <Input
                      data-testid="family-size-input"
                      type="number"
                      value={newUser.family_size}
                      onChange={(e) => setNewUser({ ...newUser, family_size: parseInt(e.target.value) })}
                      min="1"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Annual Income *</Label>
                    <Input
                      data-testid="income-input"
                      type="number"
                      value={newUser.income}
                      onChange={(e) => setNewUser({ ...newUser, income: parseFloat(e.target.value) })}
                      min="0"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Card Type *</Label>
                    <Select value={newUser.card_type} onValueChange={(value) => setNewUser({ ...newUser, card_type: value })}>
                      <SelectTrigger data-testid="card-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="APL">APL (Above Poverty Line)</SelectItem>
                        <SelectItem value="BPL">BPL (Below Poverty Line)</SelectItem>
                        <SelectItem value="Antyodaya">Antyodaya</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Phone *</Label>
                    <Input
                      data-testid="phone-input"
                      value={newUser.phone}
                      onChange={(e) => setNewUser({ ...newUser, phone: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full" data-testid="submit-user-button">Add User</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Filters */}
        <Card className="border-0 shadow-md">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  data-testid="search-input"
                  placeholder="Search by name or Aadhaar ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48" data-testid="status-filter">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                  <SelectItem value="flagged">Flagged</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Users List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading users...</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredUsers.map((user) => (
              <Card key={user.id} className="border-0 shadow-md hover:shadow-lg transition-shadow" data-testid={`user-card-${user.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                        {getStatusBadge(user.status)}
                        {getVerificationBadge(user.verification_status)}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-gray-600">
                        <div>Aadhaar: <span className="font-medium">{user.aadhaar_id}</span></div>
                        <div>Card Type: <span className="font-medium">{user.card_type}</span></div>
                        <div>District: <span className="font-medium">{user.district}, {user.state}</span></div>
                        <div>Family Size: <span className="font-medium">{user.family_size}</span></div>
                        <div>Income: <span className="font-medium">₹{user.income.toLocaleString()}</span></div>
                        <div>Phone: <span className="font-medium">{user.phone}</span></div>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      {user.verification_status === "pending" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleVerifyAadhaar(user.id)}
                          data-testid={`verify-button-${user.id}`}
                          className="border-green-200 text-green-700 hover:bg-green-50"
                        >
                          <Fingerprint className="w-4 h-4 mr-1" />
                          Verify
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleScanForFraud(user.id)}
                        data-testid={`scan-button-${user.id}`}
                        className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                      >
                        <Shield className="w-4 h-4 mr-1" />
                        Scan
                      </Button>
                      {user.status === "active" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(user.id, "suspended")}
                          data-testid={`suspend-button-${user.id}`}
                          className="border-amber-200 text-amber-700 hover:bg-amber-50"
                        >
                          <Ban className="w-4 h-4 mr-1" />
                          Suspend
                        </Button>
                      )}
                      {user.status === "suspended" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(user.id, "active")}
                          data-testid={`activate-button-${user.id}`}
                          className="border-green-200 text-green-700 hover:bg-green-50"
                        >
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Activate
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {filteredUsers.length === 0 && (
              <Card className="border-0 shadow-md">
                <CardContent className="p-12 text-center text-gray-500">
                  No users found
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Users;
