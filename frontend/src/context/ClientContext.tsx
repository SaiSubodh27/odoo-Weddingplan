import React, { createContext, useContext, useState, useEffect } from 'react';
import { Client, RegistrationStatus } from '../types/client';
import { INITIAL_CLIENTS } from '../data/mockClients';

interface ClientContextType {
  clients: Client[];
  addClient: (newClientData: Omit<Client, 'id' | 'createdAt'>) => string;
  getClient: (id: string) => Client | undefined;
  updateClientStatus: (id: string, status: RegistrationStatus) => void;
  isAuthenticated: boolean;
  login: (email: string) => void;
  logout: () => void;
  currentUser: { name: string; role: string; email: string };
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

const STORAGE_KEY = 'the_royal_knot_clients_v1';
const AUTH_KEY = 'the_royal_knot_auth_v1';

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

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(clients));
    } catch {
      // ignore
    }
  }, [clients]);

  const login = (email: string) => {
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_KEY, 'true');
    setCurrentUser(prev => ({
      ...prev,
      email: email || 'planner@theroyalknot.in',
      name: email.split('@')[0].replace('.', ' ').replace(/^\w/, c => c.toUpperCase()) || 'Agency Staff'
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

    setClients(prev => [fullClient, ...prev]);
    return newId;
  };

  const getClient = (id: string) => {
    return clients.find(c => c.id === id);
  };

  const updateClientStatus = (id: string, status: RegistrationStatus) => {
    setClients(prev =>
      prev.map(c => (c.id === id ? { ...c, status } : c))
    );
  };

  return (
    <ClientContext.Provider
      value={{
        clients,
        addClient,
        getClient,
        updateClientStatus,
        isAuthenticated,
        login,
        logout,
        currentUser
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

