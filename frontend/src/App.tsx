import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ClientProvider, useClients } from './context/ClientContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { ClientActivationPage } from './pages/ClientActivationPage';
import { ClientRegistrationPage } from './pages/ClientRegistrationPage';
import { WebsiteRegistrationPage } from './pages/WebsiteRegistrationPage';
import { ClientPortalPage } from './pages/ClientPortalPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmailInboxPage } from './pages/EmailInboxPage';
import { EnquiriesPage } from './pages/EnquiriesPage';
import { AddEnquiryPage } from './pages/AddEnquiryPage';
import { EnquiryDetailsPage } from './pages/EnquiryDetailsPage';
import { ClientsPage } from './pages/ClientsPage';
import { AddClientPage } from './pages/AddClientPage';
import { ClientDetailsPage } from './pages/ClientDetailsPage';
import { WeddingsPage } from './pages/WeddingsPage';
import { SettingsPage } from './pages/SettingsPage';

// Protected Route for Agency Employees
const StaffRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, currentUser } = useClients();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  // If a client logs in, route them to their Client Portal
  if (currentUser.role === 'Client') {
    return <Navigate to="/portal" replace />;
  }
  return <>{children}</>;
};

// Protected Route for Clients
const ClientRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useClients();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const AppContent: React.FC = () => {
  const { currentUser } = useClients();

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/activate" element={<ClientActivationPage />} />
      <Route path="/register" element={<ClientRegistrationPage />} />
      <Route path="/client-register" element={<WebsiteRegistrationPage />} />

      {/* Dedicated Client Portal (Client Side) */}
      <Route
        path="/portal"
        element={
          <ClientRoute>
            <ClientPortalPage />
          </ClientRoute>
        }
      />

      {/* Protected Routes for Agency Employees (Employee Side) */}
      <Route
        path="/"
        element={
          <StaffRoute>
            <DashboardLayout />
          </StaffRoute>
        }
      >
        <Route
          index
          element={
            <Navigate
              to={currentUser.role === 'Client' ? '/portal' : '/dashboard'}
              replace
            />
          }
        />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="inbox" element={<EmailInboxPage />} />
        <Route path="enquiries" element={<EnquiriesPage />} />
        <Route path="enquiries/new" element={<AddEnquiryPage />} />
        <Route path="enquiries/:id" element={<EnquiryDetailsPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="clients/new" element={<AddClientPage />} />
        <Route path="clients/:id" element={<ClientDetailsPage />} />
        <Route path="weddings" element={<WeddingsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Catch-all fallback */}
      <Route
        path="*"
        element={
          <Navigate
            to={currentUser.role === 'Client' ? '/portal' : '/dashboard'}
            replace
          />
        }
      />
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
