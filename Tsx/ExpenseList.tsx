// src/components/ExpenseList.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const ExpenseList: React.FC = () => {
  const { currentUser } = useAuth();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExpenses = async () => {
      if (!currentUser) {
        setError("You must be logged in to view expenses.");
        setLoading(false);
        return;
      }
      try {
        const idToken = await currentUser.getIdToken();
        const response = await axios.get('/api/user/expenses', {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        setExpenses(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch expenses.');
      } finally {
        setLoading(false);
      }
    };
    fetchExpenses();
  }, [currentUser]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="text-red-500 text-sm">{error}</p>;

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md mt-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">My Expenses</h2>
      {expenses.length === 0 ? (
        <p>No expenses recorded.</p>
      ) : (
        <table className="w-full text-sm text-left text-gray-500">
          <thead className="text-xs text-gray-700 uppercase bg-gray-50">
            <tr>
              <th className="px-4 py-2">Description</th>
              <th className="px-4 py-2">Amount</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((expense: any) => (
              <tr key={expense.id} className="bg-white border-b">
                <td className="px-4 py-2">{expense.description}</td>
                <td className="px-4 py-2">${expense.amount.toFixed(2)}</td>
                <td className="px-4 py-2">{expense.category}</td>
                <td className="px-4 py-2">{new Date(expense.date).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ExpenseList;
