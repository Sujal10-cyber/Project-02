import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import Layout from "../components/Layout";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, ArrowUpDown } from "lucide-react";

const Transactions = ({ setIsAuthenticated }) => {
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTransactions();
  }, []);

  useEffect(() => {
    filterTransactions();
  }, [transactions, searchTerm]);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`);
      setTransactions(response.data);
    } catch (error) {
      console.error("Failed to fetch transactions");
    } finally {
      setLoading(false);
    }
  };

  const filterTransactions = () => {
    if (!searchTerm) {
      setFilteredTransactions(transactions);
    } else {
      setFilteredTransactions(
        transactions.filter(t => 
          t.card_number.includes(searchTerm) ||
          t.user_id.includes(searchTerm)
        )
      );
    }
  };

  return (
    <Layout setIsAuthenticated={setIsAuthenticated}>
      <div className="space-y-6" data-testid="transactions-page">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-500 mt-1">Monitor ration distribution transactions</p>
        </div>

        {/* Search */}
        <Card className="border-0 shadow-md">
          <CardContent className="p-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                data-testid="transaction-search-input"
                placeholder="Search by card number or user ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Transactions List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading transactions...</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredTransactions.map((txn) => (
              <Card key={txn.id} className="border-0 shadow-md hover:shadow-lg transition-shadow" data-testid={`transaction-card-${txn.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">Card: {txn.card_number}</h3>
                        <Badge className="bg-green-100 text-green-700">Completed</Badge>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Shop ID:</span>
                          <span className="font-medium text-gray-900 ml-2">{txn.shop_id}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Date:</span>
                          <span className="font-medium text-gray-900 ml-2">
                            {new Date(txn.transaction_date).toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Items:</span>
                          <span className="font-medium text-gray-900 ml-2">{txn.items.length} items</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Total Amount:</span>
                          <span className="font-bold text-indigo-600 ml-2 text-base">
                            ₹{txn.total_amount.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      {txn.items.length > 0 && (
                        <div className="mt-3 pt-3 border-t">
                          <div className="text-xs text-gray-600 mb-2">Items:</div>
                          <div className="flex flex-wrap gap-2">
                            {txn.items.map((item, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {item.name} x {item.quantity}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {filteredTransactions.length === 0 && (
              <Card className="border-0 shadow-md">
                <CardContent className="p-12 text-center text-gray-500">
                  No transactions found
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Transactions;
