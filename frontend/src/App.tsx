import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ClientProvider, useClients } from './context/ClientContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ClientsPage } from './pages/ClientsPage';
import { AddClientPage } from './pages/AddClientPage';
import { ClientDetailsPage } from './pages/ClientDetailsPage';
import { WeddingsPage } from './pages/WeddingsPage';
import { SettingsPage } from './pages/SettingsPage';

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useClients();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const AppContent: React.FC = () => {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected Routes inside Dashboard Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="clients/new" element={<AddClientPage />} />
        <Route path="clients/:id" element={<ClientDetailsPage />} />
        <Route path="weddings" element={<WeddingsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Catch-all fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <ClientProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ClientProvider>
  );
};

export default App;

