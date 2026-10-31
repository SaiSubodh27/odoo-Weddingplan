import React from 'react';
import { ClientForm } from '../components/clients/ClientForm';

export const AddClientPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="pb-6 border-b border-[#E5E0D8]">
        <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
          Client Intake Protocol
        </div>
        <h1 className="font-serif text-3xl text-[#1F2421]">New Client Registration</h1>
        <p className="text-xs text-[#736F68] mt-1">
          Record couple details, destination wedding parameters, and service requirements for agency onboarding.
        </p>
      </div>

      {/* Form */}
      <ClientForm />
    </div>
  );
};

