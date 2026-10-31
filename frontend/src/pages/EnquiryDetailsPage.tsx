import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Enquiry, EnquiryStatus, EmailMessage, ClientRegistration } from '../types/enquiry';
import { enquiryApi, registrationApi } from '../services/api';
import { getEnquiryStatusBadge, getSourceIcon } from './EnquiriesPage';
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  Calendar, 
  MapPin, 
  Users, 
  Banknote, 
  Heart,
  Send, 
  Download, 
  CheckCircle, 
  Sparkles, 
  UserCheck, 
  Clock, 
  Copy, 
  Check, 
  AlertCircle,
  Paperclip,
  CheckCircle2,
  MessageSquare,
  ExternalLink,
  Edit3
} from 'lucide-react';

export const EnquiryDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [enquiry, setEnquiry] = useState<Enquiry | null>(null);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  // Email Reply state
  const [replySubject, setReplySubject] = useState('');
  const [replyBody, setReplyBody] = useState('');
  const [attachRegDoc, setAttachRegDoc] = useState(false);
  const [isSendingReply, setIsSendingReply] = useState(false);

  // Note form state
  const [newNote, setNewNote] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Client registration modal state
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [partner1Name, setPartner1Name] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [servicePackage, setServicePackage] = useState('Full-Service');
  const [weddingTheme, setWeddingTheme] = useState('Royal Rajputana Splendor');
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationResult, setRegistrationResult] = useState<any | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Online Registration State
  const [registration, setRegistration] = useState<ClientRegistration | null>(null);
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [correctionNotesText, setCorrectionNotesText] = useState('');
  const [isRequestingCorrections, setIsRequestingCorrections] = useState(false);
  const [isApprovingRegistration, setIsApprovingRegistration] = useState(false);
  const [isSendingRegLink, setIsSendingRegLink] = useState(false);
  const [copiedRegLink, setCopiedRegLink] = useState(false);
  const [googleFormUrl, setGoogleFormUrl] = useState<string>('https://docs.google.com/forms/d/e/1FAIpQLSe_theroyalknot_registration/viewform');

  const loadEnquiryAndMessages = async () => {
    if (!id) return;
    try {
      const [data, msgs, reg, cfg] = await Promise.all([
        enquiryApi.get(id),
        enquiryApi.getMessages(id).catch(() => []),
        enquiryApi.getRegistration(id).catch(() => null),
        registrationApi.getConfig().catch(() => null)
      ]);
      setEnquiry(data);
      setMessages(msgs || []);
      setRegistration(reg);
      if (cfg?.googleFormsRegistrationUrl) {
        setGoogleFormUrl(cfg.googleFormsRegistrationUrl);
      }
      setPartner1Name(data.clientName);
      if (!replySubject) {
        setReplySubject(`Re: Concerning Your Wedding Enquiry (${data.id})`);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load enquiry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEnquiryAndMessages();
  }, [id]);

  const handleStatusChange = async (newStatus: EnquiryStatus) => {
    if (!enquiry) return;
    try {
      const updated = await enquiryApi.update(enquiry.id, { status: newStatus });
      setEnquiry(updated);
      setFeedbackMessage(`Status updated to ${newStatus}`);
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update status.');
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry || !newNote.trim()) return;
    setIsAddingNote(true);
    try {
      await enquiryApi.addNote(enquiry.id, newNote.trim(), 'Maharani Gayatri Singh');
      setNewNote('');
      await loadEnquiryAndMessages();
      setFeedbackMessage('Internal note recorded.');
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to add note.');
    } finally {
      setIsAddingNote(false);
    }
  };

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry || !replyBody.trim()) return;
    setIsSendingReply(true);
    try {
      const res = await enquiryApi.reply(enquiry.id, {
        subject: replySubject.trim() || undefined,
        body: replyBody.trim(),
        attachRegistrationDocument: attachRegDoc
      });
      setReplyBody('');
      await loadEnquiryAndMessages();
      setFeedbackMessage(res.message || 'Email reply dispatched to client.');
      setTimeout(() => setFeedbackMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send reply.');
    } finally {
      setIsSendingReply(false);
    }
  };

  const handleRegisterClientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry) return;
    setIsRegistering(true);
    try {
      const result = await enquiryApi.registerClient(enquiry.id, {
        partner1Name: partner1Name.trim() || enquiry.clientName,
        partner2Name: partner2Name.trim() || 'Partner 2',
        servicePackage,
        weddingTheme,
        additionalRequirements: enquiry.requirements
      });
      setRegistrationResult(result);
      await loadEnquiryAndMessages();
      setFeedbackMessage(`Client successfully registered as #${result.client_id}! Activation link generated.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to register client.');
    } finally {
      setIsRegistering(false);
    }
  };

  const copyActivationLink = () => {
    if (!registrationResult?.activation_url) return;
    navigator.clipboard.writeText(registrationResult.activation_url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 3000);
  };

  const handleSendRegistrationLink = async () => {
    if (!enquiry) return;
    setIsSendingRegLink(true);
    try {
      const res = await enquiryApi.sendRegistrationLink(enquiry.id);
      setFeedbackMessage(res.message || 'Online registration invitation dispatched to client.');
      await loadEnquiryAndMessages();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to dispatch registration link.');
    } finally {
      setIsSendingRegLink(false);
    }
  };

  const getEffectiveGoogleFormLink = () => {
    if (!enquiry) return googleFormUrl;
    return googleFormUrl.includes('?')
      ? `${googleFormUrl}&enquiry_ref=${encodeURIComponent(enquiry.id)}`
      : `${googleFormUrl}?enquiry_ref=${encodeURIComponent(enquiry.id)}`;
  };

  const handleCopyRegistrationLink = () => {
    const url = getEffectiveGoogleFormLink();
    navigator.clipboard.writeText(url);
    setCopiedRegLink(true);
    setTimeout(() => setCopiedRegLink(false), 3000);
  };

  const handleReviewRegistration = async () => {
    if (!enquiry) return;
    try {
      await enquiryApi.reviewRegistration(enquiry.id, { reviewedBy: 'Maharani Gayatri Singh' });
      setFeedbackMessage('Registration dossier marked as Under Review.');
      await loadEnquiryAndMessages();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update review status.');
    }
  };

  const handleApproveRegistration = async () => {
    if (!enquiry) return;
    setIsApprovingRegistration(true);
    try {
      const res = await enquiryApi.approveRegistration(enquiry.id, 'Maharani Gayatri Singh');
      setRegistrationResult(res);
      setFeedbackMessage('Client registration approved! Dossier and activation link dispatched.');
      await loadEnquiryAndMessages();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to approve registration.');
    } finally {
      setIsApprovingRegistration(false);
    }
  };

  const handleRequestCorrections = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry || !correctionNotesText.trim()) return;
    setIsRequestingCorrections(true);
    try {
      const res = await enquiryApi.requestCorrections(enquiry.id, {
        staffName: 'Maharani Gayatri Singh',
        correctionNotes: correctionNotesText.trim()
      });
      setFeedbackMessage(res.message || 'Correction request dispatched to client.');
      setShowCorrectionModal(false);
      setCorrectionNotesText('');
      await loadEnquiryAndMessages();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to request corrections.');
    } finally {
      setIsRequestingCorrections(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-12 text-center text-xs text-[#8C877D]">
        Retrieving Royal Dossier...
      </div>
    );
  }

  if (!enquiry) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-8 text-center space-y-4">
        <div className="text-sm font-serif text-[#94352D]">Enquiry Dossier Not Found</div>
        <Link
          to="/enquiries"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider"
        >
          <ArrowLeft size={14} />
          <span>Return to Directory</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link & Actions top bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/enquiries"
          className="inline-flex items-center gap-2 text-xs uppercase tracking-wider text-[#736F68] hover:text-[#1F2421] transition-colors"
        >
          <ArrowLeft size={14} className="text-[#9E7D3B]" />
          <span>Return to Enquiries</span>
        </Link>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status selector */}
          <div className="flex items-center gap-1.5 text-xs bg-[#FFFFFF] border border-[#E5E0D8] px-2.5 py-1.5">
            <span className="text-[10px] uppercase tracking-wider text-[#8C877D]">Status:</span>
            <select
              value={enquiry.status}
              onChange={(e) => handleStatusChange(e.target.value as EnquiryStatus)}
              className="text-xs bg-transparent text-[#1F2421] font-medium focus:outline-none"
            >
              <option value="New">New</option>
              <option value="Contacted">Contacted</option>
              <option value="Registration Link Sent">Registration Link Sent</option>
              <option value="Registration Submitted">Registration Submitted</option>
              <option value="Under Review">Under Review</option>
              <option value="Approved">Approved</option>
              <option value="Corrections Requested">Corrections Requested</option>
              <option value="Registered">Registered</option>
              <option value="Closed">Closed</option>
            </select>
          </div>

          {/* Quick Review / Approval Actions */}
          {registration && registration.status !== 'APPROVED' && enquiry.status !== 'Registered' && (
            <button
              onClick={handleApproveRegistration}
              disabled={isApprovingRegistration}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2D5A3C] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#23462f] transition-colors"
            >
              <UserCheck size={13} className="text-[#D9C496]" />
              <span>{isApprovingRegistration ? 'Approving...' : 'Approve & Activate'}</span>
            </button>
          )}

          {/* Manual Register Modal Action */}
          {!registration && enquiry.status !== 'Registered' && (
            <button
              onClick={() => setShowRegisterModal(true)}
              className="flex items-center gap-2 px-4 py-1.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors"
            >
              <UserCheck size={14} className="text-[#D9C496]" />
              <span>Register Client</span>
            </button>
          )}
        </div>
      </div>

      {/* Feedback & Error banners */}
      {errorMessage && (
        <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={15} />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-xs font-bold uppercase ml-4">✕</button>
        </div>
      )}

      {feedbackMessage && (
        <div className="p-4 bg-[#F2F7F2] border border-[#CDE3CD] text-[#245928] text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} />
            <span>{feedbackMessage}</span>
          </div>
          <button onClick={() => setFeedbackMessage(null)} className="text-xs font-bold uppercase ml-4">✕</button>
        </div>
      )}

      {/* Registered Client Banner */}
      {enquiry.clientId && (
        <div className="p-4 bg-[#F2F7F2] border border-[#CDE3CD] text-[#245928] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <CheckCircle size={16} />
            <span>This enquiry has been formalized into Client Dossier <strong>#{enquiry.clientId}</strong>.</span>
          </div>
          <Link
            to={`/clients/${enquiry.clientId}`}
            className="text-xs font-semibold text-[#1F2421] hover:underline"
          >
            Open Client Dossier →
          </Link>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Inquiry Specs & Registration Document Workflow */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Inquiry Overview */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8] mb-6">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Celebration Specifications</h2>
              </div>
              <span className={`px-2.5 py-1 text-[10px] uppercase tracking-wider font-semibold border ${getEnquiryStatusBadge(enquiry.status)}`}>
                {enquiry.status}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Inbound Channel</span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  {getSourceIcon(enquiry.enquirySource)}
                  <span>{enquiry.enquirySource} Intake</span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Target Wedding Date</span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <Calendar size={14} className="text-[#9E7D3B]" />
                  <span>{enquiry.weddingDate || 'Date Not Finalized'}</span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Preferred Palace / Destination</span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <MapPin size={14} className="text-[#9E7D3B]" />
                  <span>{enquiry.weddingLocation || 'Rajasthan Heritage Venue'}</span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Expected Guests & Budget</span>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1F2421]">
                  <Users size={14} className="text-[#9E7D3B]" />
                  <span>{enquiry.expectedGuestCount || '—'} Guests</span>
                  <span className="text-[#8C877D]">·</span>
                  <Banknote size={14} className="text-[#9E7D3B]" />
                  <span>₹ {enquiry.estimatedBudget || 'Not Disclosed'}</span>
                </div>
              </div>

              <div className="sm:col-span-2 pt-2 border-t border-[#E5E0D8]">
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Client Message / Vision</span>
                <p className="text-xs text-[#1F2421] bg-[#FAF8F5] p-3 border border-[#E5E0D8] leading-relaxed">
                  {enquiry.requirements || 'No specific requests noted during initial contact.'}
                </p>
              </div>
            </div>
          </div>

          {/* Online Client Registration & Verification Module */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Online Client Registration & Verification</h2>
              </div>
              <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 border ${
                registration?.status === 'APPROVED' ? 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9]' :
                registration?.status === 'SUBMITTED' ? 'bg-[#F0F4FA] text-[#1D4E89] border-[#B5CEEB] font-bold' :
                registration?.status === 'UNDER_REVIEW' ? 'bg-[#FDF6E2] text-[#8C6D1F] border-[#E8D49E]' :
                registration?.status === 'CORRECTIONS_REQUESTED' ? 'bg-[#FFF3E8] text-[#B85D1B] border-[#FAD3B4]' :
                'bg-[#FAF8F5] text-[#8C877D] border-[#E5E0D8]'
              }`}>
                {registration ? registration.status.replace('_', ' ') : (enquiry.status === 'Registration Link Sent' ? 'Link Sent' : 'Awaiting Submission')}
              </span>
            </div>

            {/* Google Forms Registration Link Bar */}
            <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <span className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider flex items-center gap-1.5">
                  <Mail size={13} className="text-[#9E7D3B]" />
                  <span>Google Forms Client Registration Link</span>
                </span>
                {enquiry.registrationSentAt && (
                  <span className="text-[10px] text-[#2D5A3C] flex items-center gap-1 font-medium">
                    <CheckCircle size={11} /> Invitation Dispatched: {new Date(enquiry.registrationSentAt).toLocaleDateString('en-IN')}
                  </span>
                )}
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={getEffectiveGoogleFormLink()}
                  className="flex-1 px-3 py-2 text-xs bg-[#FFFFFF] border border-[#E5E0D8] text-[#4A4640] font-mono focus:outline-none"
                />
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleCopyRegistrationLink}
                    className="px-3 py-2 bg-[#FFFFFF] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#1F2421] hover:bg-[#F2EFE8] flex items-center gap-1.5 transition-colors"
                  >
                    {copiedRegLink ? <Check size={12} className="text-[#2D5A3C]" /> : <Copy size={12} />}
                    <span>{copiedRegLink ? 'Copied' : 'Copy Form Link'}</span>
                  </button>

                  <a
                    href={getEffectiveGoogleFormLink()}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 bg-[#FFFFFF] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#1F2421] hover:bg-[#F2EFE8] flex items-center gap-1.5 transition-colors"
                  >
                    <ExternalLink size={12} />
                    <span>Open Form</span>
                  </a>

                  <button
                    onClick={handleSendRegistrationLink}
                    disabled={isSendingRegLink}
                    className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <Send size={12} className="text-[#D9C496]" />
                    <span>{isSendingRegLink ? 'Sending...' : 'Send Form Link via Email'}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Submitted Client Dossier Display */}
            {registration ? (
              <div className="border border-[#E5E0D8] bg-[#FFFFFF] p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-[#E5E0D8] pb-3">
                  <div className="flex items-center gap-2">
                    <Heart size={15} className="text-[#9E7D3B]" />
                    <h3 className="font-serif text-base text-[#1F2421]">
                      Client Submitted Dossier: {registration.fullName} {registration.partnerName ? `& ${registration.partnerName}` : ''}
                    </h3>
                    <span className="px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[9px] uppercase tracking-wider text-[#9E7D3B] font-semibold">
                      Google Forms Response
                    </span>
                  </div>
                  <span className="text-[10px] text-[#8C877D]">
                    Submitted: {new Date(registration.submittedAt).toLocaleString('en-IN')}
                  </span>
                </div>

                {/* Parameters Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Primary Client</span>
                    <span className="font-semibold text-[#1F2421]">{registration.fullName}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Partner Name</span>
                    <span className="font-semibold text-[#1F2421]">{registration.partnerName || '—'}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Contact Phone</span>
                    <span className="font-semibold text-[#1F2421]">{registration.phone}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Target Date</span>
                    <span className="font-semibold text-[#1F2421]">{registration.weddingDate || 'TBD'}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Destination Venue</span>
                    <span className="font-semibold text-[#1F2421]">{registration.weddingLocation || 'TBD'}</span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Guests & Budget</span>
                    <span className="font-semibold text-[#1F2421]">
                      {registration.expectedGuestCount || '—'} Guests · ₹ {registration.estimatedBudget ? Number(registration.estimatedBudget).toLocaleString('en-IN') : '—'}
                    </span>
                  </div>

                  <div className="sm:col-span-2">
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Ceremonial Events Requested</span>
                    <div className="flex flex-wrap gap-1.5">
                      {registration.weddingEvents ? (
                        registration.weddingEvents.split(',').map((ev, i) => (
                          <span key={i} className="px-2 py-0.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[11px] text-[#1F2421]">
                            {ev.trim()}
                          </span>
                        ))
                      ) : (
                        <span className="text-[#8C877D]">None specified</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Retainer Tier</span>
                    <span className="font-semibold text-[#9E7D3B]">{registration.servicePackage}</span>
                  </div>

                  {registration.preferredTheme && (
                    <div className="sm:col-span-3">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Preferred Aesthetic & Theme</span>
                      <span className="text-[#1F2421]">{registration.preferredTheme}</span>
                    </div>
                  )}

                  {registration.preferences && (
                    <div className="sm:col-span-3 pt-2 border-t border-[#E5E0D8]">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Confidential Client Notes & Requests</span>
                      <p className="bg-[#FAF8F5] p-3 border border-[#E5E0D8] text-[#1F2421] leading-relaxed">
                        {registration.preferences}
                      </p>
                    </div>
                  )}

                  {registration.correctionNotes && (
                    <div className="sm:col-span-3 p-3 bg-[#FFF3E8] border border-[#FAD3B4] text-[#B85D1B]">
                      <span className="text-[10px] uppercase tracking-wider font-bold block mb-1">Corrections Requested by Staff:</span>
                      <p className="leading-relaxed">{registration.correctionNotes}</p>
                    </div>
                  )}
                </div>

                {/* Employee Review Controls */}
                <div className="pt-4 border-t border-[#E5E0D8] flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-[#8C877D]">
                    {registration.status === 'APPROVED' ? (
                      <span className="text-[#2D5A3C] font-semibold flex items-center gap-1.5">
                        <CheckCircle size={14} /> Approved by {registration.reviewedBy || 'Staff'} on {registration.reviewedAt ? new Date(registration.reviewedAt).toLocaleDateString('en-IN') : 'Recently'}
                      </span>
                    ) : registration.status === 'UNDER_REVIEW' ? (
                      <span className="text-[#8C6D1F]">Under review by {registration.reviewedBy || 'Staff'}</span>
                    ) : (
                      <span>Awaiting staff verification</span>
                    )}
                  </div>

                  {registration.status !== 'APPROVED' && (
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => setShowCorrectionModal(true)}
                        className="px-3 py-1.5 bg-[#FFFFFF] border border-[#E5E0D8] text-xs uppercase tracking-wider text-[#B85D1B] hover:bg-[#FFF3E8] flex items-center gap-1.5"
                      >
                        <Edit3 size={13} />
                        <span>Request Corrections</span>
                      </button>

                      {registration.status !== 'UNDER_REVIEW' && (
                        <button
                          onClick={handleReviewRegistration}
                          className="px-3 py-1.5 bg-[#FAF8F5] border border-[#9E7D3B] text-xs uppercase tracking-wider text-[#8C6D1F] hover:bg-[#FDF6E2]"
                        >
                          <span>Mark Under Review</span>
                        </button>
                      )}

                      <button
                        onClick={handleApproveRegistration}
                        disabled={isApprovingRegistration}
                        className="px-4 py-1.5 bg-[#2D5A3C] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#23462f] flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <UserCheck size={13} className="text-[#D9C496]" />
                        <span>{isApprovingRegistration ? 'Approving...' : 'Approve & Send Activation Link'}</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Awaiting submission state */
              <div className="p-6 border border-dashed border-[#E5E0D8] bg-[#FAF8F5] text-center space-y-3">
                <Clock size={24} className="mx-auto text-[#9E7D3B]" />
                <h4 className="font-serif text-sm uppercase tracking-wider text-[#1F2421]">
                  Awaiting Client Online Submission
                </h4>
                <p className="text-xs text-[#736F68] max-w-md mx-auto leading-relaxed">
                  An automated thank-you email with the online registration link has been dispatched to <strong className="text-[#1F2421]">{enquiry.email}</strong>. Once submitted, the complete wedding parameters will appear here for your review and approval.
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleSendRegistrationLink}
                    disabled={isSendingRegLink}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733]"
                  >
                    <Send size={12} className="text-[#D9C496]" />
                    <span>{isSendingRegLink ? 'Sending...' : 'Re-send Invitation Link Email'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Historical Attachments if any */}
            {enquiry.documents && enquiry.documents.length > 0 && (
              <div className="pt-4 border-t border-[#E5E0D8]">
                <div className="text-[10px] font-semibold text-[#8C877D] uppercase tracking-wider mb-2">
                  Historical Email Attachments ({enquiry.documents.length})
                </div>
                <div className="space-y-1.5">
                  {enquiry.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-2.5 border border-[#E5E0D8] bg-[#FAF8F5] flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <Paperclip size={12} className="text-[#9E7D3B]" />
                        <span className="font-medium text-[#1F2421]">{doc.originalFilename}</span>
                        <span className="text-[10px] text-[#8C877D]">({(doc.fileSize / 1024).toFixed(1)} KB)</span>
                      </div>
                      <a
                        href={enquiryApi.getDownloadUrl(enquiry.id, doc.id)}
                        className="text-[10px] uppercase text-[#9E7D3B] hover:underline flex items-center gap-1 font-semibold"
                      >
                        <Download size={10} />
                        <span>Download</span>
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Module 1 & 2: Email Conversation & Replies */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <MessageSquare size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Email Conversation & Client Replies</h2>
              </div>
              <span className="text-[10px] uppercase tracking-wider text-[#8C877D] bg-[#FAF8F5] border border-[#E5E0D8] px-2 py-0.5">
                {messages.length} Message(s)
              </span>
            </div>

            {/* Conversation Thread */}
            <div className="space-y-4">
              {messages.length === 0 ? (
                <div className="text-[11px] text-[#8C877D] italic p-4 border border-dashed border-[#E5E0D8] text-center">
                  No direct email messages recorded in this conversation yet. Send an email below or sync Gmail.
                </div>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.id}
                    className={`p-4 border text-xs space-y-2 ${
                      m.direction === 'outgoing'
                        ? 'bg-[#FAF8F5] border-[#E5E0D8] ml-4 sm:ml-8 border-l-4 border-l-[#1F2421]'
                        : 'bg-[#FFFFFF] border-[#E5E0D8] mr-4 sm:mr-8 border-l-4 border-l-[#9E7D3B]'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px] pb-2 border-b border-[#E5E0D8]/60">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-[9px] uppercase tracking-widest font-bold ${
                          m.direction === 'outgoing'
                            ? 'bg-[#1F2421] text-[#FAF8F5]'
                            : 'bg-[#9E7D3B] text-[#FAF8F5]'
                        }`}>
                          {m.direction === 'outgoing' ? 'Agency Outbound' : 'Client Inbound'}
                        </span>
                        <span className="font-medium text-[#1F2421]">
                          {m.direction === 'outgoing' ? m.senderName || 'The Royal Knot' : m.senderName || m.senderEmail}
                        </span>
                        <span className="text-[#8C877D]">({m.senderEmail})</span>
                      </div>

                      <div className="flex items-center gap-2 text-[#8C877D]">
                        <Clock size={11} />
                        <span>{new Date(m.createdAt).toLocaleString('en-IN')}</span>
                      </div>
                    </div>

                    <div className="font-semibold text-xs text-[#1F2421]">
                      {m.subject}
                    </div>

                    <div className="text-[#5C5850] leading-relaxed whitespace-pre-wrap bg-[#FFFFFF] p-3 border border-[#E5E0D8]/50">
                      {m.bodyText || '(No plain text message content)'}
                    </div>

                    {/* Email Attachments */}
                    {m.attachments && m.attachments.length > 0 && (
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <span className="text-[10px] uppercase tracking-wider text-[#8C877D] flex items-center gap-1">
                          <Paperclip size={11} /> Attachment(s):
                        </span>
                        {m.attachments.map((att) => (
                          <a
                            key={att.id}
                            href={att.downloadUrl || `http://localhost:8000/api/v1/emails/${m.id}/attachments/${att.id}/download`}
                            className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                          >
                            <Paperclip size={10} className="text-[#9E7D3B]" />
                            <span>{att.originalFilename}</span>
                            <span className="text-[#8C877D]">({(att.fileSize / 1024).toFixed(1)} KB)</span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* In-place Reply Form */}
            <form onSubmit={handleSendReply} className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] space-y-3 text-xs">
              <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider flex items-center justify-between">
                <span>Reply to Client via Email</span>
                <span className="text-[10px] text-[#8C877D]">Sender: saisubodh6@gmail.com</span>
              </div>

              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Subject</label>
                <input
                  type="text"
                  value={replySubject}
                  onChange={(e) => setReplySubject(e.target.value)}
                  className="w-full px-3 py-1.5 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Message Body *</label>
                <textarea
                  rows={4}
                  required
                  value={replyBody}
                  onChange={(e) => setReplyBody(e.target.value)}
                  placeholder="Draft your concierge reply to the client..."
                  className="w-full px-3 py-2 bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-[#5C5850]">
                  <input
                    type="checkbox"
                    checked={attachRegDoc}
                    onChange={(e) => setAttachRegDoc(e.target.checked)}
                    className="border-[#E5E0D8]"
                  />
                  <span>Attach Client Registration Form to this reply</span>
                </label>

                <button
                  type="submit"
                  disabled={isSendingReply || !replyBody.trim()}
                  className="flex items-center gap-2 px-5 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] disabled:opacity-50"
                >
                  <Send size={12} className="text-[#D9C496]" />
                  <span>{isSendingReply ? 'Sending Reply...' : 'Send Email Reply'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Internal Notes History */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
            <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
              <Clock size={16} className="text-[#9E7D3B]" />
              <h2 className="font-serif text-xl text-[#1F2421]">Internal Staff Notes & Log</h2>
            </div>

            {/* Note form */}
            <form onSubmit={handleAddNote} className="space-y-2">
              <textarea
                rows={2}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add a new update or call summary..."
                className="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#1F2421]"
              />
              <button
                type="submit"
                disabled={isAddingNote || !newNote.trim()}
                className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider disabled:opacity-50 font-semibold"
              >
                {isAddingNote ? 'Adding...' : 'Post Staff Note'}
              </button>
            </form>

            {/* Notes timeline */}
            <div className="space-y-3 pt-2">
              {enquiry.notesHistory && enquiry.notesHistory.length > 0 ? (
                enquiry.notesHistory.map((n) => (
                  <div key={n.id} className="p-3 border-l-2 border-[#9E7D3B] bg-[#FAF8F5] text-xs">
                    <div className="flex items-center justify-between text-[10px] text-[#8C877D] mb-1">
                      <span className="font-semibold text-[#1F2421] uppercase">{n.author}</span>
                      <span>{new Date(n.createdAt).toLocaleString('en-IN')}</span>
                    </div>
                    <p className="text-[#5C5850] leading-relaxed whitespace-pre-wrap">{n.content}</p>
                  </div>
                ))
              ) : (
                <div className="text-[11px] text-[#8C877D] italic">No previous notes logged.</div>
              )}
            </div>
          </div>

        </div>

        {/* Right Column (1 Col): Contact & Meta */}
        <div className="space-y-6">
          
          {/* Client Contact Card */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-4">
            <h3 className="font-serif text-lg font-semibold text-[#1F2421] pb-3 border-b border-[#E5E0D8]">
              Primary Contact
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Client Name</span>
                <div className="text-sm font-semibold text-[#1F2421]">{enquiry.clientName}</div>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Email</span>
                <a href={`mailto:${enquiry.email}`} className="flex items-center gap-1.5 text-[#1F2421] hover:text-[#9E7D3B]">
                  <Mail size={13} className="text-[#9E7D3B]" />
                  <span>{enquiry.email}</span>
                </a>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block mb-1">Phone / WhatsApp</span>
                <a href={`tel:${enquiry.phone}`} className="flex items-center gap-1.5 text-[#1F2421] hover:text-[#9E7D3B]">
                  <Phone size={13} className="text-[#9E7D3B]" />
                  <span>{enquiry.phone}</span>
                </a>
              </div>
            </div>
          </div>

          {/* Concierge Assignment */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-3 text-xs">
            <h3 className="font-serif text-lg font-semibold text-[#1F2421] pb-3 border-b border-[#E5E0D8]">
              Concierge Desk
            </h3>
            <div className="flex justify-between py-1 border-b border-[#E5E0D8]/60">
              <span className="text-[#8C877D]">Assigned Staff:</span>
              <span className="font-medium text-[#1F2421]">{enquiry.assignedStaff || 'Gayatri Singh'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#E5E0D8]/60">
              <span className="text-[#8C877D]">Operating Hubs:</span>
              <span className="text-[#1F2421]">Jaipur & Udaipur</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#8C877D]">Created Date:</span>
              <span className="text-[#1F2421]">{new Date(enquiry.createdAt).toLocaleDateString('en-IN')}</span>
            </div>
          </div>

        </div>
      </div>

      {/* Registration Confirmation Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border-2 border-[#1F2421] p-6 sm:p-8 max-w-lg w-full space-y-6">
            <div className="pb-3 border-b border-[#E5E0D8]">
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
                Dossier Formalization
              </div>
              <h3 className="font-serif text-2xl text-[#1F2421]">Register Client from Enquiry</h3>
              <p className="text-xs text-[#736F68] mt-1">
                This will create a registered Client Dossier and initialize a pending portal account with a secure activation link.
              </p>
            </div>

            {registrationResult ? (
              <div className="space-y-4 text-xs">
                <div className="p-4 bg-[#F2F7F2] border border-[#CDE3CD] text-[#245928] space-y-2">
                  <div className="font-semibold text-sm flex items-center gap-1.5">
                    <CheckCircle2 size={16} />
                    <span>Client Successfully Registered!</span>
                  </div>
                  <p>Client Reference: <strong>#{registrationResult.client_id}</strong></p>
                  <p>Account status: <strong>PENDING_ACTIVATION</strong></p>
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">
                    Client Account Activation Link (Expires in 72 hours)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={registrationResult.activation_url}
                      className="w-full px-2.5 py-1.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[11px] font-mono"
                    />
                    <button
                      type="button"
                      onClick={copyActivationLink}
                      className="px-3 py-1.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider flex items-center gap-1 font-semibold"
                    >
                      {copiedLink ? <Check size={13} className="text-[#2D5A3C]" /> : <Copy size={13} />}
                      <span>{copiedLink ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                </div>

                <div className="pt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setShowRegisterModal(false)}
                    className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleRegisterClientSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Partner 1 Full Name *</label>
                  <input
                    type="text"
                    required
                    value={partner1Name}
                    onChange={(e) => setPartner1Name(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Partner 2 Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Kabir Oberoi"
                    value={partner2Name}
                    onChange={(e) => setPartner2Name(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Service Tier Selection</label>
                  <select
                    value={servicePackage}
                    onChange={(e) => setServicePackage(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                  >
                    <option value="Full-Service">Full-Service Royal Concierge</option>
                    <option value="Partial-Service">Partial-Service Planning</option>
                    <option value="Day-of Coordination">Executive Day-of Coordination</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Initial Design Theme</label>
                  <input
                    type="text"
                    value={weddingTheme}
                    onChange={(e) => setWeddingTheme(e.target.value)}
                    placeholder="e.g. Royal Marwar Heritage & Twilight Candles"
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                  />
                </div>

                <div className="pt-4 flex items-center justify-end gap-3 border-t border-[#E5E0D8]">
                  <button
                    type="button"
                    onClick={() => setShowRegisterModal(false)}
                    className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] text-xs uppercase"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isRegistering}
                    className="px-6 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold disabled:opacity-50"
                  >
                    {isRegistering ? 'Registering...' : 'Confirm Registration'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Correction Request Modal */}
      {showCorrectionModal && (
        <div className="fixed inset-0 z-50 bg-[#1F2421]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] w-full max-w-lg p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <Edit3 size={16} className="text-[#9E7D3B]" />
                <h3 className="font-serif text-lg text-[#1F2421]">Request Registration Corrections</h3>
              </div>
              <button
                onClick={() => setShowCorrectionModal(false)}
                className="text-[#8C877D] hover:text-[#1F2421] text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#5C5850] leading-relaxed">
              Detail the exact clarifications or corrections required from <strong className="text-[#1F2421]">{enquiry.clientName}</strong>. An automated notification with an update link will be dispatched to <strong className="text-[#1F2421]">{enquiry.email}</strong>.
            </p>

            <form onSubmit={handleRequestCorrections} className="space-y-4 text-xs">
              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1 font-semibold">
                  Director Notes / Clarifications Required *
                </label>
                <textarea
                  rows={4}
                  required
                  value={correctionNotesText}
                  onChange={(e) => setCorrectionNotesText(e.target.value)}
                  placeholder="e.g. Kindly confirm whether your guest estimate includes international attendees requiring private palace transfers..."
                  className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B] leading-relaxed"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setShowCorrectionModal(false)}
                  className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] text-xs uppercase"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRequestingCorrections || !correctionNotesText.trim()}
                  className="px-6 py-2 bg-[#B85D1B] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold disabled:opacity-50 hover:bg-[#9E4D14]"
                >
                  {isRequestingCorrections ? 'Dispatching...' : 'Dispatch Correction Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
