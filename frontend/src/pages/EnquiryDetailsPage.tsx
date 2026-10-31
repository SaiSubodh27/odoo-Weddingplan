import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Enquiry, EnquiryStatus } from '../types/enquiry';
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
  AlertCircle
} from 'lucide-react';

export const EnquiryDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [enquiry, setEnquiry] = useState<Enquiry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  // Note form state
  const [newNote, setNewNote] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Document upload state
  const [uploadType, setUploadType] = useState<'sent_to_client' | 'completed_by_client'>('completed_by_client');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Client registration modal / form state
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [partner1Name, setPartner1Name] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [servicePackage, setServicePackage] = useState('Full-Service');
  const [weddingTheme, setWeddingTheme] = useState('Royal Rajputana Splendor');
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationResult, setRegistrationResult] = useState<any | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const loadEnquiry = async () => {
    if (!id) return;
    try {
      const data = await enquiryApi.get(id);
      setEnquiry(data);
      setPartner1Name(data.clientName);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load enquiry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEnquiry();
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
      await loadEnquiry();
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
      await loadEnquiry();
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
      await loadEnquiry();
      setFeedbackMessage(res.message || 'Document marked as received.');
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to mark document as received.');
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enquiry || !selectedFile) return;
    setIsUploading(true);
    try {
      await enquiryApi.uploadDocument(enquiry.id, selectedFile, uploadType);
      setSelectedFile(null);
      await loadEnquiry();
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
    setErrorMessage(null);
    try {
      const result = await enquiryApi.registerClient(enquiry.id, {
        partner1Name,
        partner2Name,
        servicePackage,
        weddingTheme
      });
      setRegistrationResult(result);
      await loadEnquiry();
      setFeedbackMessage(result.message);
    } catch (err: any) {
      setErrorMessage(err.message || 'Client registration failed.');
    } finally {
      setIsRegistering(false);
    }
  };

  const copyActivationLink = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-[#FFFFFF] border border-[#E5E0D8] text-xs text-[#736F68]">
        Loading enquiry dossier...
      </div>
    );
  }

  if (!enquiry) {
    return (
      <div className="p-12 text-center bg-[#FFFFFF] border border-[#E5E0D8] space-y-4">
        <h2 className="font-serif text-2xl text-[#1F2421]">Enquiry Not Found</h2>
        <p className="text-xs text-[#736F68]">The enquiry reference #{id} could not be located.</p>
        <button
          onClick={() => navigate('/enquiries')}
          className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider"
        >
          Return to Enquiries
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E0D8]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enquiries')}
            className="p-2 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] text-[#1F2421]"
            title="Back to Enquiries"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium">
              <span>Inbound Dossier</span>
              <span>·</span>
              <span className="font-mono">Ref: {enquiry.id}</span>
            </div>
            <h1 className="font-serif text-3xl text-[#1F2421]">
              {enquiry.clientName}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status selector */}
          <div className="flex items-center gap-2 border border-[#E5E0D8] bg-[#FFFFFF] px-3 py-1.5">
            <span className="text-[10px] uppercase tracking-wider text-[#736F68]">Status:</span>
            <select
              value={enquiry.status}
              onChange={(e) => handleStatusChange(e.target.value as EnquiryStatus)}
              className="text-xs font-semibold bg-transparent border-none text-[#1F2421] focus:ring-0 cursor-pointer"
            >
              <option value="New">New</option>
              <option value="Contacted">Contacted</option>
              <option value="Registration Document Sent">Registration Document Sent</option>
              <option value="Registration Received">Registration Received</option>
              <option value="Registered">Registered</option>
              <option value="Closed">Closed</option>
            </select>
          </div>

          {/* Register Client CTA */}
          {enquiry.status !== 'Registered' ? (
            <button
              onClick={() => setShowRegisterModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-[#1F2421] hover:bg-[#343733] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold border border-[#1F2421] transition-colors"
            >
              <UserCheck size={14} className="text-[#D9C496]" />
              <span>Register Client</span>
            </button>
          ) : (
            <Link
              to={`/clients/${enquiry.clientId}`}
              className="flex items-center gap-2 px-4 py-2 bg-[#EBF3ED] text-[#2D5A3C] border border-[#C3D9C9] text-xs uppercase tracking-wider font-semibold"
            >
              <CheckCircle size={14} />
              <span>View Client #{enquiry.clientId}</span>
            </Link>
          )}
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 bg-[#FBF1F0] border border-[#E9C3C0] text-[#94352D] text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="underline text-[11px]">Dismiss</button>
        </div>
      )}

      {feedbackMessage && (
        <div className="p-3 bg-[#EBF3ED] border border-[#C3D9C9] text-[#2D5A3C] text-xs font-medium uppercase tracking-wider flex items-center gap-2">
          <CheckCircle size={15} />
          <span>{feedbackMessage}</span>
        </div>
      )}

      {/* Registration Success Banner */}
      {registrationResult && (
        <div className="bg-[#FFFFFF] border-2 border-[#9E7D3B] p-6 space-y-3">
          <div className="flex items-center gap-2 text-[#9E7D3B]">
            <Sparkles size={18} />
            <h3 className="font-serif text-lg font-semibold text-[#1F2421]">Client Registered Successfully</h3>
          </div>
          <p className="text-xs text-[#736F68]">
            Client reference <strong>#{registrationResult.client_id}</strong> created and user account initialized in pending activation.
          </p>
          <div className="bg-[#FAF8F5] p-3 border border-[#E5E0D8] text-xs space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-[#8C877D] font-medium">Unique Activation URL (Sent via Email):</div>
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[#1F2421] break-all">{registrationResult.activation_url}</span>
              <button
                onClick={() => copyActivationLink(registrationResult.activation_url)}
                className="shrink-0 p-1.5 border border-[#E5E0D8] bg-[#FFFFFF] hover:bg-[#FAF8F5] flex items-center gap-1 text-[11px]"
              >
                {copiedLink ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
                <span>{copiedLink ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>
          <div className="pt-2">
            <Link
              to={`/clients/${registrationResult.client_id}`}
              className="text-xs font-semibold text-[#1F2421] hover:underline"
            >
              Open Client Dossier →
            </Link>
          </div>
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

          {/* Module 2 & 3: Registration Document Exchange Workflow */}
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
                  <span>Step 1: Registration Document</span>
                  {enquiry.registrationSentAt && (
                    <span className="text-[10px] text-[#2D5A3C] flex items-center gap-1">
                      <CheckCircle size={11} /> Sent
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
                    <Download size={12} />
                    <span>View / Print Form</span>
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

              {/* Step 2: Completed Document Receipt */}
              <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5] space-y-3">
                <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider flex items-center justify-between">
                  <span>Step 2: Completed Dossier</span>
                  {enquiry.registrationReceivedAt && (
                    <span className="text-[10px] text-[#2D5A3C] flex items-center gap-1">
                      <CheckCircle size={11} /> Received
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#736F68] leading-relaxed">
                  Record when the client returns their filled and signed registration document.
                </p>
                <div className="pt-1">
                  <button
                    onClick={handleMarkReceived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] uppercase tracking-wider bg-[#FFFFFF] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                  >
                    <CheckCircle size={12} className="text-[#2D5A3C]" />
                    <span>Mark Document Received</span>
                  </button>
                </div>
                {enquiry.registrationReceivedAt && (
                  <div className="text-[10px] text-[#8C877D]">
                    Received on: {new Date(enquiry.registrationReceivedAt).toLocaleString('en-IN')}
                  </div>
                )}
              </div>
            </div>

            {/* Document Upload Area */}
            <form onSubmit={handleFileUpload} className="p-4 border border-[#E5E0D8] bg-[#FFFFFF] space-y-3">
              <div className="text-xs font-semibold text-[#1F2421] uppercase tracking-wider">
                Upload Document Attachment
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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

                <div className="sm:col-span-2">
                  <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Choose File (PDF, DOCX, PNG, JPG)</label>
                  <div className="flex gap-2">
                    <input
                      type="file"
                      onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                      className="text-xs file:mr-2 file:py-1 file:px-3 file:border file:border-[#E5E0D8] file:text-xs file:bg-[#FAF8F5]"
                    />
                    <button
                      type="submit"
                      disabled={!selectedFile || isUploading}
                      className="px-4 py-1.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider disabled:opacity-50 flex items-center gap-1"
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
                Attached Files & Dossiers ({enquiry.documents?.length || 0})
              </div>
              {enquiry.documents && enquiry.documents.length > 0 ? (
                <div className="space-y-2">
                  {enquiry.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3 border border-[#E5E0D8] bg-[#FAF8F5] flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-medium text-[#1F2421]">{doc.originalFilename}</div>
                        <div className="text-[10px] text-[#8C877D] mt-0.5">
                          Type: <span className="uppercase">{doc.documentType.replace(/_/g, ' ')}</span> · {(doc.fileSize / 1024).toFixed(1)} KB · {new Date(doc.createdAt).toLocaleDateString('en-IN')}
                        </div>
                      </div>
                      <a
                        href={enquiryApi.getDownloadUrl(enquiry.id, doc.id)}
                        className="flex items-center gap-1 px-2.5 py-1 text-[11px] uppercase tracking-wider text-[#1F2421] bg-[#FFFFFF] border border-[#E5E0D8] hover:bg-[#F2EFE8]"
                      >
                        <Download size={11} />
                        <span>Download</span>
                      </a>
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
                className="px-4 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider disabled:opacity-50"
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
                    <p className="text-[#5C5850] leading-relaxed">{n.content}</p>
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
                  className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] text-xs uppercase tracking-wider"
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
          </div>
        </div>
      )}
    </div>
  );
};
