import React, { createContext, useContext, useState, useEffect } from 'react';
import { Client, RegistrationStatus } from '../types/client';
import { INITIAL_CLIENTS } from '../data/mockClients';

interface ClientContextType {
  clients: Client[];
  addClient: (newClientData: Omit<Client, 'id' | 'createdAt'>) => string;
  getClient: (id: string) => Client | undefined;
  updateClientStatus: (id: string, status: RegistrationStatus) => void;
  updateClient: (id: string, changes: Partial<Client>) => void;
  isAuthenticated: boolean;
  login: (email: string, details?: { name?: string; role?: string }) => void;
  logout: () => void;
  currentUser: { name: string; role: string; email: string };
  isBackendConnected: boolean;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

const STORAGE_KEY = 'the_royal_knot_clients_v1';
const AUTH_KEY = 'the_royal_knot_auth_v1';
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
      return true; // Default logged in or ready
    }
  });

  const [currentUser, setCurrentUser] = useState({
    name: 'Maharani Gayatri Singh',
    role: 'Principal Wedding Planner',
    email: 'gayatri@theroyalknot.in'
  });

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

  const login = (email: string, details?: { name?: string; role?: string }) => {
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_KEY, 'true');
    setCurrentUser(prev => ({
      ...prev,
      email: email || 'planner@theroyalknot.in',
      name: details?.name || email.split('@')[0].replace('.', ' ').replace(/^\w/, c => c.toUpperCase()) || 'Agency Staff',
      role: details?.role || (email.includes('theroyalknot.in') ? 'Principal Wedding Planner' : 'Client')
    }));
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem(AUTH_KEY);
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

    // Optimistic state update
    setClients(prev => [fullClient, ...prev]);

    // Asynchronously persist to PostgreSQL backend
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
      .catch(() => {
        // Graceful fallback to client state
      });

    return newId;
  };

  const getClient = (id: string) => {
    return clients.find(c => c.id === id);
  };

  const updateClient = (id: string, changes: Partial<Client>) => {
    setClients(prev => prev.map(c => c.id === id ? {...c,...changes,id:c.id,createdAt:c.createdAt} : c));
  };
  const updateClientStatus = (id: string, status: RegistrationStatus) => {
    setClients(prev =>
      prev.map(c => (c.id === id ? { ...c, status } : c))
    );

    // Sync status change to backend
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

