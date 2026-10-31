import React, { createContext, useContext, useState, useEffect } from 'react';
import { Client, RegistrationStatus } from '../types/client';
import { INITIAL_CLIENTS } from '../data/mockClients';

interface LoginDetails {
  name?: string;
  role?: string;
  clientId?: string;
  hasCompletedDetails?: boolean;
  hasSignedAgreement?: boolean;
  agreementId?: string;
  token?: string;
}

interface ClientContextType {
  clients: Client[];
  addClient: (newClientData: Omit<Client, 'id' | 'createdAt'>) => string;
  getClient: (id: string) => Client | undefined;
  updateClientStatus: (id: string, status: RegistrationStatus) => void;
  updateClient: (id: string, changes: Partial<Client>) => void;
  isAuthenticated: boolean;
  hasCompletedDetails: boolean;
  setHasCompletedDetails: (val: boolean) => void;
  hasSignedAgreement: boolean;
  setHasSignedAgreement: (val: boolean) => void;
  agreementId: string | null;
  setAgreementId: (id: string | null) => void;
  login: (email: string, details?: LoginDetails) => void;
  logout: () => void;
  currentUser: { name: string; role: string; email: string; clientId?: string };
  isBackendConnected: boolean;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

const STORAGE_KEY = 'the_royal_knot_clients_v1';
const AUTH_KEY = 'the_royal_knot_auth_v1';
const TOKEN_KEY = 'the_royal_knot_token_v1';
const USER_KEY = 'the_royal_knot_user_v1';
const CLIENT_ID_KEY = 'the_royal_knot_client_id_v1';
const DETAILS_COMPLETED_KEY = 'the_royal_knot_details_completed_v1';
const AGREEMENT_SIGNED_KEY = 'the_royal_knot_agreement_signed_v1';
const AGREEMENT_ID_KEY = 'the_royal_knot_agreement_id_v1';
const API_BASE = 'http://localhost:8000/api/v1';

export const ClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [clients, setClients] = useState<Client[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // fallback
    }
    return INITIAL_CLIENTS;
  });

  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      return localStorage.getItem(AUTH_KEY) === 'true';
    } catch {
      return true;
    }
  });

  const [hasCompletedDetails, setHasCompletedDetailsState] = useState<boolean>(() => {
    try {
      return localStorage.getItem(DETAILS_COMPLETED_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const [hasSignedAgreement, setHasSignedAgreementState] = useState<boolean>(() => {
    try {
      return localStorage.getItem(AGREEMENT_SIGNED_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const [agreementId, setAgreementIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(AGREEMENT_ID_KEY);
    } catch {
      return null;
    }
  });

  const setHasCompletedDetails = (val: boolean) => {
    setHasCompletedDetailsState(val);
    try {
      localStorage.setItem(DETAILS_COMPLETED_KEY, val ? 'true' : 'false');
    } catch {
      // ignore
    }
  };

  const setHasSignedAgreement = (val: boolean) => {
    setHasSignedAgreementState(val);
    try {
      localStorage.setItem(AGREEMENT_SIGNED_KEY, val ? 'true' : 'false');
    } catch {
      // ignore
    }
  };

  const setAgreementId = (id: string | null) => {
    setAgreementIdState(id);
    try {
      if (id) {
        localStorage.setItem(AGREEMENT_ID_KEY, id);
      } else {
        localStorage.removeItem(AGREEMENT_ID_KEY);
      }
    } catch {
      // ignore
    }
  };

  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem(USER_KEY);
      if (savedUser) return JSON.parse(savedUser);
    } catch (_) {}
    return {
      name: 'Maharani Gayatri Singh',
      role: 'Principal Wedding Planner',
      email: 'gayatri@theroyalknot.in',
      clientId: undefined as string | undefined
    };
  });

  // Global interceptor for 403 AGREEMENT_REQUIRED
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      if (response.status === 403) {
        const isAgr = response.headers.get("x-agreement-required") === "true";
        if (isAgr && window.location.pathname !== "/agreement") {
          window.location.href = "/agreement";
        }
      }
      return response;
    };
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  // Check and fetch from PostgreSQL backend
  useEffect(() => {
    const syncBackend = async () => {
      try {
        const res = await fetch(`${API_BASE}/clients?page=1&page_size=100`);
        if (res.ok) {
          const data = await res.json();
          if (data && Array.isArray(data.items) && data.items.length > 0) {
            setClients(data.items);
          }
          setIsBackendConnected(true);
        } else {
          setIsBackendConnected(false);
        }
      } catch {
        setIsBackendConnected(false);
      }
    };
    syncBackend();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(clients));
    } catch {
      // ignore
    }
  }, [clients]);

  const login = (email: string, details?: LoginDetails) => {
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_KEY, 'true');

    if (details?.token) {
      localStorage.setItem(TOKEN_KEY, details.token);
    }

    const isStaff = email.includes('theroyalknot.in') || details?.role === 'staff' || details?.role === 'Principal Wedding Planner';
    const completedDetails = isStaff ? true : (details?.hasCompletedDetails ?? false);
    const signed = isStaff ? true : (details?.hasSignedAgreement ?? false);

    setHasCompletedDetails(completedDetails);
    setHasSignedAgreement(signed);
    if (details?.agreementId) {
      setAgreementId(details.agreementId);
    }

    const userObj = {
      email: email || 'planner@theroyalknot.in',
      name: details?.name || email.split('@')[0].replace('.', ' ').replace(/^\w/, c => c.toUpperCase()) || 'Agency Staff',
      role: details?.role || (isStaff ? 'Principal Wedding Planner' : 'Client Workspace'),
      clientId: details?.clientId || localStorage.getItem(CLIENT_ID_KEY) || undefined
    };
    setCurrentUser(userObj);
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(userObj));
      if (details?.clientId) {
        localStorage.setItem(CLIENT_ID_KEY, details.clientId);
      }
    } catch (_) {}
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(DETAILS_COMPLETED_KEY);
    localStorage.removeItem(AGREEMENT_SIGNED_KEY);
    localStorage.removeItem(AGREEMENT_ID_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(CLIENT_ID_KEY);
  };

  const addClient = (newClientData: Omit<Client, 'id' | 'createdAt'>): string => {
    const nextNumber = 80 + clients.length + 1;
    const newId = `TRK-2026-0${nextNumber}`;
    const today = new Date().toISOString().split('T')[0];

    const fullClient: Client = {
      ...newClientData,
      id: newId,
      createdAt: today
    };

    setClients(prev => [fullClient, ...prev]);

    fetch(`${API_BASE}/clients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newClientData)
    })
      .then(async (res) => {
        if (res.ok) {
          const created = await res.json();
          if (created && created.id) {
            setClients(prev => prev.map(c => c.id === newId ? { ...c, id: created.id } : c));
          }
        }
      })
      .catch(() => {});

    return newId;
  };

  const getClient = (id: string) => {
    return clients.find(c => c.id === id);
  };

  const updateClient = (id: string, changes: Partial<Client>) => {
    setClients(prev => prev.map(c => c.id === id ? { ...c, ...changes, id: c.id, createdAt: c.createdAt } : c));
  };

  const updateClientStatus = (id: string, status: RegistrationStatus) => {
    setClients(prev => prev.map(c => (c.id === id ? { ...c, status } : c)));

    fetch(`${API_BASE}/clients/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    }).catch(() => {});
  };

  return (
    <ClientContext.Provider
      value={{
        clients,
        addClient,
        getClient,
        updateClientStatus,
        updateClient,
        isAuthenticated,
        hasCompletedDetails,
        setHasCompletedDetails,
        hasSignedAgreement,
        setHasSignedAgreement,
        agreementId,
        setAgreementId,
        login,
        logout,
        currentUser,
        isBackendConnected
      }}
    >
      {children}
    </ClientContext.Provider>
  );
};

export const useClients = () => {
  const context = useContext(ClientContext);
  if (!context) {
    throw new Error('useClients must be used within a ClientProvider');
  }
  return context;
};
