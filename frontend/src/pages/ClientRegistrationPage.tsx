import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { registrationApi } from '../services/api';
import { ExternalLink, Sparkles } from 'lucide-react';

export const ClientRegistrationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const enquiryRef = searchParams.get('enquiry_ref') || searchParams.get('ref') || '';

  const [targetUrl, setTargetUrl] = useState<string>('https://docs.google.com/forms/d/e/1FAIpQLSe_theroyalknot_registration/viewform');

  useEffect(() => {
    let isMounted = true;

    async function fetchFormUrlAndRedirect() {
      try {
        const config = await registrationApi.getConfig();
        let formUrl = config.googleFormsRegistrationUrl || 'https://docs.google.com/forms/d/e/1FAIpQLSe_theroyalknot_registration/viewform';

        if (enquiryRef) {
          formUrl += (formUrl.includes('?') ? '&' : '?') + `enquiry_ref=${encodeURIComponent(enquiryRef)}`;
        } else if (token) {
          formUrl += (formUrl.includes('?') ? '&' : '?') + `token=${encodeURIComponent(token)}`;
        }

        if (isMounted) {
          setTargetUrl(formUrl);
          // Automatic redirection to Google Forms
          window.location.href = formUrl;
        }
      } catch (err) {
        // Fallback default
        if (isMounted) {
          window.location.href = targetUrl;
        }
      }
    }

    fetchFormUrlAndRedirect();

    return () => {
      isMounted = false;
    };
  }, [enquiryRef, token]);

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#1F2421] flex flex-col justify-center items-center p-6 selection:bg-[#9E7D3B] selection:text-white">
      <div className="max-w-lg w-full bg-[#FFFFFF] border border-[#E5E0D8] p-8 sm:p-12 text-center shadow-sm">
        {/* Crest Brand Header */}
        <div className="inline-flex items-center justify-center w-12 h-12 bg-[#FAF8F5] border border-[#E5E0D8] text-[#9E7D3B] mb-6">
          <Sparkles size={20} />
        </div>

        <div className="text-[10px] tracking-[0.25em] uppercase text-[#9E7D3B] font-medium mb-2">
          The Royal Knot Concierge
        </div>
        <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[#1F2421] mb-3">
          Client Registration Dossier
        </h1>

        <p className="text-xs text-[#736F68] leading-relaxed mb-8">
          We use Google Forms for client wedding registration. You are being redirected to our official celebration registration dossier...
        </p>

        <div className="py-4 border-t border-b border-[#E5E0D8] mb-8">
          <div className="text-[11px] text-[#9E7D3B] animate-pulse font-medium">
            Redirecting to Google Forms...
          </div>
        </div>

        <a
          href={targetUrl}
          className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-6 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.2em] font-medium hover:bg-[#9E7D3B] transition-colors"
        >
          <span>Open Google Registration Form</span>
          <ExternalLink size={14} />
        </a>

        <div className="mt-8 text-[11px] text-[#8C877D]">
          Bespoke Destination Weddings · Jaipur & Udaipur
        </div>
      </div>
    </div>
  );
};
