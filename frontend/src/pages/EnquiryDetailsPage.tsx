import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Enquiry, EnquiryStatus, EmailMessage } from '../types/enquiry';
import { enquiryApi } from '../services/api';
import { getEnquiryStatusBadge, getSourceIcon } from './EnquiriesPage';
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  Calendar, 
  MapPin, 
  Users, 
  Banknote, 
  FileText, 
  Send, 
  Download, 
  Upload, 
  CheckCircle, 
  Sparkles, 
  UserCheck, 
  Clock, 
  Copy, 
  Check, 
  AlertCircle,
  Paperclip,
  CheckCircle2,
  FileSearch,
  MessageSquare,
  Eye
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

  // Document review state
  const [isReviewingDoc, setIsReviewingDoc] = useState(false);

  // Document upload state
  const [uploadType, setUploadType] = useState<'sent_to_client' | 'completed_by_client'>('completed_by_client');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Client registration modal state
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [partner1Name, setPartner1Name] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [servicePackage, setServicePackage] = useState('Full-Service');
  const [weddingTheme, setWeddingTheme] = useState('Royal Rajputana Splendor');
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationResult, setRegistrationResult] = useState<any | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const loadEnquiryAndMessages = async () => {
    if (!id) return;
    try {
      const [data, msgs] = await Promise.all([
        enquiryApi.get(id),
        enquiryApi.getMessages(id).catch(() => [])
      ]);
      setEnquiry(data);
      setMessages(msgs || []);
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

  const handleSendDocumentEmail = async () => {
    if (!enquiry) return;
    try {
      const res = await enquiryApi.sendDocument(enquiry.id);
      await loadEnquiryAndMessages();
      setFeedbackMessage(res.message || 'Registration document email dispatched.');
      setTimeout(() => setFeedbackMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send registration document email.');
    }
  };

  const handleMarkReceived = async () => {
    if (!enquiry) return;
    try {
      const res = await enquiryApi.markDocumentReceived(enquiry.id);
      await loadEnquiryAndMessages();
      setFeedbackMessage(res.message || 'Document marked as received.');
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to mark document as received.');
    }
  };

  const handleMarkReviewed = async () => {
    if (!enquiry) return;
    setIsReviewingDoc(true);
    try {
      const res = await enquiryApi.markDocumentReviewed(enquiry.id, undefined, 'Maharani Gayatri Singh');
      await loadEnquiryAndMessages();
      setFeedbackMessage(res.message || 'Document marked as reviewed. Enquiry moved to Under Review.');
      setTimeout(() => setFeedbackMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to mark document reviewed.');
    } finally {
      setIsReviewingDoc(false);
    }
  };

  const handleMarkSpecificDocReviewed = async (docId: string) => {
    if (!enquiry) return;
    setIsReviewingDoc(true);
    try {
      const res = await enquiryApi.markDocumentReviewed(enquiry.id, docId, 'Maharani Gayatri Singh');
      await loadEnquiryAndMessages();
      setFeedbackMessage(res.message || 'Document marked as reviewed. Enquiry moved to Under Review.');
      setTimeout(() => setFeedbackMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to mark document reviewed.');
    } finally {
      setIsReviewingDoc(false);
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

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry || !selectedFile) return;
    setIsUploading(true);
    try {
      await enquiryApi.uploadDocument(enquiry.id, selectedFile, uploadType);
      setSelectedFile(null);
      await loadEnquiryAndMessages();
      setFeedbackMessage(`Document '${selectedFile.name}' uploaded successfully.`);
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
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
              <option value="Registration Document Sent">Registration Document Sent</option>
              <option value="Registration Received">Registration Received</option>
              <option value="Under Review">Under Review</option>
              <option value="Registered">Registered</option>
              <option value="Closed">Closed</option>
            </select>
          </div>

          {/* Mark Reviewed Action */}
          {enquiry.status === 'Registration Received' && (
            <button
              onClick={handleMarkReviewed}
              disabled={isReviewingDoc}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#FAF8F5] border border-[#9E7D3B] text-[#8C6D1F] text-xs uppercase tracking-wider font-semibold hover:bg-[#FDF6E2] transition-colors"
            >
              <FileSearch size={13} className="text-[#9E7D3B]" />
              <span>{isReviewingDoc ? 'Reviewing...' : 'Mark Document Reviewed'}</span>
            </button>
          )}

          {/* Register Client Action */}
          {enquiry.status !== 'Registered' && (
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
                <span className="text-[10px] uppercase tracking-wider text-[#8C877D] block">Expected Guests and Budget</span>
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

          {/* Registration Document Exchange Workflow */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Registration Document Exchange</h2>
              </div>
              <span className="text-[10px] uppercase tracking-wider text-[#8C877D] bg-[#FAF8F5] border border-[#E5E0D8] px-2 py-0.5">
                Staff Protocol
              </span>
            </div>

            {/* Workflow steps */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Step 1: Blank Document & Dispatch */}
              <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] space-y-3">
                <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider flex items-center justify-between">
                  <span>Step 1: Registration Dossier</span>
                  {enquiry.registrationSentAt && (
                    <span className="text-[10px] text-[#2D5A3C] flex items-center gap-1 font-medium">
                      <CheckCircle size={11} /> Dispatched
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#736F68] leading-relaxed">
                  Generate or download the formal pre-filled Royal Knot registration dossier to send to the client.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <a
                    href={enquiryApi.getTemplateUrl(enquiry.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] uppercase tracking-wider bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                  >
                    <Eye size={12} />
                    <span>View / Print Form</span>
                  </a>

                  <a
                    href={enquiryApi.getTemplateDownloadUrl(enquiry.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] uppercase tracking-wider bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                  >
                    <Download size={12} />
                    <span>Download File</span>
                  </a>

                  <button
                    onClick={handleSendDocumentEmail}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] uppercase tracking-wider bg-[#1F2421] text-[#FAF8F5] hover:bg-[#343733]"
                  >
                    <Send size={12} className="text-[#D9C496]" />
                    <span>Send via Email</span>
                  </button>
                </div>
                {enquiry.registrationSentAt && (
                  <div className="text-[10px] text-[#8C877D]">
                    Dispatched on: {new Date(enquiry.registrationSentAt).toLocaleString('en-IN')}
                  </div>
                )}
              </div>

              {/* Step 2: Completed Document Receipt & Review */}
              <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] space-y-3">
                <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider flex items-center justify-between">
                  <span>Step 2: Completed Dossier</span>
                  {enquiry.registrationReceivedAt && (
                    <span className="text-[10px] text-[#2D5A3C] flex items-center gap-1 font-medium">
                      <CheckCircle size={11} /> {enquiry.status === 'Under Review' || enquiry.status === 'Registered' ? 'Reviewed' : 'Received'}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#736F68] leading-relaxed">
                  {enquiry.status === 'Under Review'
                    ? 'Registration document reviewed and verified. Proceed with formal client registration.'
                    : enquiry.status === 'Registration Received'
                    ? 'Client returned their completed document. Review all submitted parameters before registering.'
                    : 'Clients return completed forms by replying to the email thread with attachment.'}
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {enquiry.status === 'Registration Received' ? (
                    <button
                      onClick={handleMarkReviewed}
                      disabled={isReviewingDoc}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 text-[11px] uppercase tracking-wider bg-[#1F2421] text-[#FAF8F5] hover:bg-[#343733] font-semibold"
                    >
                      <FileSearch size={12} className="text-[#D9C496]" />
                      <span>{isReviewingDoc ? 'Reviewing...' : 'Mark Document Reviewed'}</span>
                    </button>
                  ) : enquiry.status === 'Under Review' ? (
                    <button
                      onClick={() => setShowRegisterModal(true)}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 text-[11px] uppercase tracking-wider bg-[#2D5A3C] text-[#FAF8F5] hover:bg-[#23462f] font-semibold"
                    >
                      <UserCheck size={12} className="text-[#D9C496]" />
                      <span>Proceed to Register Client</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleMarkReceived}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] uppercase tracking-wider bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                    >
                      <CheckCircle size={12} className="text-[#2D5A3C]" />
                      <span>Mark Received Manually</span>
                    </button>
                  )}
                </div>
                {enquiry.registrationReceivedAt && (
                  <div className="text-[10px] text-[#8C877D]">
                    Received on: {new Date(enquiry.registrationReceivedAt).toLocaleString('en-IN')}
                    {enquiry.registrationReviewedAt && (
                      <span> · Reviewed on: {new Date(enquiry.registrationReviewedAt).toLocaleString('en-IN')}</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Document Upload Area */}
            <form onSubmit={handleFileUpload} className="p-4 border border-[#E5E0D8] bg-[#FFFFFF] space-y-3">
              <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Upload Document Attachment
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Document Type</label>
                  <select
                    value={uploadType}
                    onChange={(e: any) => setUploadType(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                  >
                    <option value="completed_by_client">Completed by Client</option>
                    <option value="sent_to_client">Sent to Client</option>
                  </select>
                </div>

                <div className="min-w-0">
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Choose File (PDF, DOCX, HTML, PNG, JPG)</label>
                  <div className="flex flex-col gap-3 min-w-0">
                    <input
                      type="file"
                      onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                      className="block w-full min-w-0 max-w-full text-xs file:mr-2 file:py-2 file:px-3 file:border file:border-[#E5E0D8] file:text-xs file:bg-[#FAF8F5]"
                    />
                    <button
                      type="submit"
                      disabled={!selectedFile || isUploading}
                      className="self-start px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider disabled:opacity-50 inline-flex items-center gap-2 font-semibold"
                    >
                      <Upload size={12} />
                      <span>{isUploading ? 'Uploading...' : 'Upload'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </form>

            {/* Uploaded Documents List */}
            <div>
              <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider mb-2">
                Attached Files and Dossiers ({enquiry.documents?.length || 0})
              </div>
              {enquiry.documents && enquiry.documents.length > 0 ? (
                <div className="space-y-2">
                  {enquiry.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3 border border-[#E5E0D8] bg-[#FAF8F5] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <div className="font-medium text-[#1F2421] flex flex-wrap items-center gap-2">
                          <span>{doc.originalFilename}</span>
                          {doc.isReviewed ? (
                            <span className="text-[10px] bg-[#EBF3ED] text-[#2D5A3C] px-1.5 py-0.2 border border-[#C3D9C9] font-medium">
                              Reviewed by {doc.reviewedBy || 'Staff'}
                            </span>
                          ) : doc.documentType === 'completed_by_client' ? (
                            <span className="text-[10px] bg-[#FFF8E6] text-[#8C6D1F] px-1.5 py-0.2 border border-[#E8D49E] font-medium">
                              Pending Review
                            </span>
                          ) : null}
                        </div>
                        <div className="text-[10px] text-[#8C877D] mt-0.5">
                          Type: <span className="uppercase">{doc.documentType.replace(/_/g, ' ')}</span> · {(doc.fileSize / 1024).toFixed(1)} KB · {new Date(doc.createdAt).toLocaleDateString('en-IN')}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={enquiryApi.getViewUrl(enquiry.id, doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 px-2.5 py-1 text-[11px] uppercase tracking-wider text-[#1F2421] bg-[#FFFFFF] border border-[#E5E0D8] hover:bg-[#F2EFE8]"
                        >
                          <Eye size={11} />
                          <span>View</span>
                        </a>
                        <a
                          href={enquiryApi.getDownloadUrl(enquiry.id, doc.id)}
                          className="flex items-center gap-1 px-2.5 py-1 text-[11px] uppercase tracking-wider text-[#1F2421] bg-[#FFFFFF] border border-[#E5E0D8] hover:bg-[#F2EFE8]"
                        >
                          <Download size={11} />
                          <span>Download</span>
                        </a>
                        {doc.documentType === 'completed_by_client' && !doc.isReviewed && (
                          <button
                            onClick={() => handleMarkSpecificDocReviewed(doc.id)}
                            disabled={isReviewingDoc}
                            className="flex items-center gap-1 px-2.5 py-1 text-[11px] uppercase tracking-wider text-[#8C6D1F] bg-[#FAF8F5] border border-[#9E7D3B] hover:bg-[#FDF6E2] font-semibold"
                          >
                            <FileSearch size={11} />
                            <span>Mark Reviewed</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[11px] text-[#8C877D] italic p-3 border border-dashed border-[#E5E0D8] text-center">
                  No files uploaded yet for this enquiry.
                </div>
              )}
            </div>
          </div>

          {/* Module 1 & 2: Email Conversation & Replies */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-2">
                <MessageSquare size={16} className="text-[#9E7D3B]" />
                <h2 className="font-serif text-xl text-[#1F2421]">Email Conversation and Client Replies</h2>
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
              <h2 className="font-serif text-xl text-[#1F2421]">Internal Staff Notes and Log</h2>
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
              <span className="text-[#1F2421]">Jaipur and Udaipur</span>
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
                  <div className="flex flex-col gap-3 min-w-0">
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
                    placeholder="e.g. Royal Marwar Heritage and Twilight Candles"
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
    </div>
  );
};
