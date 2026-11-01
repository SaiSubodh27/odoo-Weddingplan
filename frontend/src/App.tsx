import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ClientProvider, useClients } from './context/ClientContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { ClientActivationPage } from './pages/ClientActivationPage';
import { ClientRegistrationPage } from './pages/ClientRegistrationPage';
import { ClientAgreementSigningPage } from './pages/ClientAgreementSigningPage';
import { ClientPortalPage } from './pages/ClientPortalPage';
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
import { WeddingProjectPage } from './pages/WeddingProjectPage';
import { VendorsPage } from './pages/VendorsPage';
import { VendorDirectoryPage } from './pages/VendorDirectoryPage';
import { VendorPortalPage } from './pages/VendorPortalPage';
import { FounderPortalPage } from './pages/FounderPortalPage';
import { SettingsPage } from './pages/SettingsPage';
import { BigDayLivePage } from './pages/BigDayLivePage';
import { ClientIntakePage } from './pages/ClientIntakePage';

// Protected Route wrapper with intake details and agreement gate enforcement
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, currentUser, hasCompletedDetails, hasSignedAgreement } = useClients();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const isClient = currentUser.role.toLowerCase().includes('client');
  if (isClient) {
    // Stage 1: Take user details first
    if (!hasCompletedDetails && location.pathname !== '/client-intake') {
      return <Navigate to="/client-intake" replace />;
    }
    // Stage 2: Give service agreement after taking user details
    if (hasCompletedDetails && !hasSignedAgreement && location.pathname !== '/agreement') {
      return <Navigate to="/agreement" replace />;
    }
    // Restrict clients from viewing internal agency/staff management pages
    const employeeRoutes = [
      '/', '/dashboard', '/inbox', '/enquiries', '/clients', '/projects',
      '/weddings', '/vendors', '/vendor-directory', '/quotations',
      '/settings', '/founder-portal', '/big-day'
    ];
    if (employeeRoutes.some(r => location.pathname === r || location.pathname.startsWith(r + '/'))) {
      return <Navigate to="/client-portal" replace />;
    }
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
      <Route path="/vendor-portal" element={<VendorPortalPage />} />
      <Route path="/founder-portal" element={<FounderPortalPage />} />

      {/* Stage 1: Client Wedding Details Intake */}
      <Route
        path="/client-intake"
        element={
          <ProtectedRoute>
            <ClientIntakePage />
          </ProtectedRoute>
        }
      />

      {/* Stage 2: Mandatory Service Agreement Signing Gateway */}
      <Route
        path="/agreement"
        element={
          <ProtectedRoute>
            <ClientAgreementSigningPage />
          </ProtectedRoute>
        }
      />

      {/* Stage 3: Client Celebration Portal */}
      <Route
        path="/client-portal"
        element={
          <ProtectedRoute>
            <ClientPortalPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes inside Dashboard Layout (Staff & Agency Management) */}
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
        <Route path="weddings" element={<WeddingsPage />} />
        <Route path="weddings/:id" element={<WeddingProjectPage />} />
        <Route path="weddings/:id/big-day" element={<BigDayLivePage />} />
        <Route path="big-day" element={<BigDayLivePage />} />
        <Route path="weddings-calendar" element={<WeddingsPage />} />
        <Route path="vendors" element={<VendorsPage />} />
        <Route path="vendor-directory" element={<VendorDirectoryPage />} />
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
    <BrowserRouter>
      <ClientProvider>
        <AppContent />
      </ClientProvider>
    </BrowserRouter>
  );
};

export default App;
