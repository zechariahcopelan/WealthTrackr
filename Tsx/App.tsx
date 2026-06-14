// src/App.tsx
import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import AddIncomeForm from './components/AddIncomeForm';
import AddExpenseForm from './components/AddExpenseForm';
import ExpenseList from './components/ExpenseList';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-100 py-6">
        <div className="container mx-auto">
          <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">Personal Finance Tracker</h1>
          <AddIncomeForm />
          <AddExpenseForm />
          <ExpenseList />
        </div>
      </div>
    </AuthProvider>
  );
};

export default App;
