import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ClientProvider, useClients } from './context/ClientContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { ClientActivationPage } from './pages/ClientActivationPage';
import { ClientRegistrationPage } from './pages/ClientRegistrationPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmailInboxPage } from './pages/EmailInboxPage';
import { EnquiriesPage } from './pages/EnquiriesPage';
import { AddEnquiryPage } from './pages/AddEnquiryPage';
import { EnquiryDetailsPage } from './pages/EnquiryDetailsPage';
import { ClientsPage } from './pages/ClientsPage';
import { AddClientPage } from './pages/AddClientPage';
import { ClientDetailsPage } from './pages/ClientDetailsPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ProjectDetailsPage } from './pages/ProjectDetailsPage';
import { WeddingsPage } from './pages/WeddingsPage';
import { WeddingPlanningPage } from './pages/WeddingPlanningPage';
import { VendorsPage } from './pages/VendorsPage';
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
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/activate" element={<ClientActivationPage />} />
      <Route path="/register" element={<ClientRegistrationPage />} />

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
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:id" element={<ProjectDetailsPage />} />
        <Route path="projects/:id/planning" element={<WeddingPlanningPage />} />
        <Route path="weddings" element={<ProjectsPage />} />
        <Route path="weddings-calendar" element={<WeddingsPage />} />
        <Route path="vendors" element={<VendorsPage />} />
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
