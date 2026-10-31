import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ClientProvider, useClients } from './context/ClientContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { ClientActivationPage } from './pages/ClientActivationPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmailInboxPage } from './pages/EmailInboxPage';
import { EnquiriesPage } from './pages/EnquiriesPage';
import { AddEnquiryPage } from './pages/AddEnquiryPage';
import { EnquiryDetailsPage } from './pages/EnquiryDetailsPage';
import { ClientsPage } from './pages/ClientsPage';
import { AddClientPage } from './pages/AddClientPage';
import { ClientDetailsPage } from './pages/ClientDetailsPage';
import { WeddingsPage } from './pages/WeddingsPage';
import { WeddingProjectPage } from './pages/WeddingProjectPage';
import { SettingsPage } from './pages/SettingsPage';
import { VendorDirectoryPage } from './pages/VendorDirectoryPage';
import { VendorPortalPage } from './pages/VendorPortalPage';
import { FounderPortalPage } from './pages/FounderPortalPage';

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
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/activate" element={<ClientActivationPage />} />
      <Route path="/vendor-portal" element={<VendorPortalPage />} />
      <Route path="/founder-portal" element={<FounderPortalPage />} />

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
        <Route path="inbox" element={<EmailInboxPage />} />
        <Route path="enquiries" element={<EnquiriesPage />} />
        <Route path="enquiries/new" element={<AddEnquiryPage />} />
        <Route path="enquiries/:id" element={<EnquiryDetailsPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="clients/new" element={<AddClientPage />} />
        <Route path="clients/:id" element={<ClientDetailsPage />} />
        <Route path="weddings" element={<WeddingsPage />} />
        <Route path="weddings/:id" element={<WeddingProjectPage />} />
        <Route path="vendors" element={<VendorDirectoryPage />} />
        <Route path="quotations" element={<VendorDirectoryPage />} />
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


