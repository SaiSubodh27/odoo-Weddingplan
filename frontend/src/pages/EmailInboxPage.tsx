import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { emailApi, enquiryApi } from '../services/api';
import { EmailMessage, EmailStatus, Enquiry } from '../types/enquiry';
import { 
  Inbox, 
  RefreshCw, 
  Mail, 
  Sparkles, 
  Paperclip, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Trash2, 
  Plus, 
  Link2, 
  Search, 
  Send 
} from 'lucide-react';

export const EmailInboxPage: React.FC = () => {
  const navigate = useNavigate();

  const [status, setStatus] = useState<EmailStatus | null>(null);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState<'unclassified' | 'all' | 'simulate'>('unclassified');
  const [searchTerm, setSearchTerm] = useState('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Association modal state
  const [associatingMsg, setAssociatingMsg] = useState<EmailMessage | null>(null);
  const [selectedEnquiryId, setSelectedEnquiryId] = useState('');
  const [isAssociating, setIsAssociating] = useState(false);

  // Convert to enquiry modal state
  const [convertingMsg, setConvertingMsg] = useState<EmailMessage | null>(null);
  const [clientNameInput, setClientNameInput] = useState('');
  const [isConverting, setIsConverting] = useState(false);

  // Simulation form state
  const [simSenderEmail, setSimSenderEmail] = useState('princess.ananya@jaipurheritage.in');
  const [simSenderName, setSimSenderName] = useState('Ananya Rathore');
  const [simSubject, setSimSubject] = useState('Destination Wedding Inquiry - Rambagh Palace Jaipur');
  const [simBody, setSimBody] = useState('Greetings, we are planning a 3-day royal palace celebration in Jaipur for 450 guests. We would love to discuss planning packages and dates.');
  const [simFile, setSimFile] = useState<File | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusData, inboxData, enqData] = await Promise.all([
        emailApi.getStatus(),
        emailApi.listInbox({ limit: 100 }),
        enquiryApi.list({ pageSize: 100 }),
      ]);
      setStatus(statusData);
      setMessages(inboxData.items || []);
      setEnquiries(enqData.items || []);
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Failed to load inbox data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSyncMailbox = async () => {
    setIsSyncing(true);
    setFeedback(null);
    try {
      const res = await emailApi.sync();
      if (res.success) {
        setFeedback({ type: 'success', text: res.message || 'Gmail mailbox synchronized successfully.' });
      } else {
        setFeedback({ 
          type: 'error', 
          text: res.message || 'IMAP is not configured with a live App Password. You can use the Simulation console below to test.' 
        });
      }
      await loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Sync failed.' });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleConvertToEnquiry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!convertingMsg) return;
    setIsConverting(true);
    try {
      const enq = await emailApi.convertToEnquiry(convertingMsg.id, {
        clientName: clientNameInput.trim() || undefined
      });
      setFeedback({ type: 'success', text: `Enquiry #${enq.id} created from email!` });
      setConvertingMsg(null);
      await loadData();
      navigate(`/enquiries/${enq.id}`);
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Failed to convert to enquiry.' });
    } finally {
      setIsConverting(false);
    }
  };

  const handleAssociate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!associatingMsg || !selectedEnquiryId) return;
    setIsAssociating(true);
    try {
      await emailApi.associate(associatingMsg.id, selectedEnquiryId);
      setFeedback({ type: 'success', text: `Email associated with enquiry #${selectedEnquiryId}.` });
      setAssociatingMsg(null);
      setSelectedEnquiryId('');
      await loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Failed to associate email.' });
    } finally {
      setIsAssociating(false);
    }
  };

  const handleIgnore = async (msgId: string) => {
    try {
      await emailApi.ignore(msgId);
      setFeedback({ type: 'success', text: 'Email marked as ignored.' });
      await loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Failed to ignore email.' });
    }
  };

  const handleSimulateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSimulating(true);
    setFeedback(null);

    const formData = new FormData();
    formData.append('sender_email', simSenderEmail.trim());
    formData.append('sender_name', simSenderName.trim());
    formData.append('subject', simSubject.trim());
    formData.append('body_text', simBody.trim());
    if (simFile) {
      formData.append('file', simFile);
    }

    try {
      const res = await emailApi.simulate(formData);
      if (res.processed) {
        setFeedback({ 
          type: 'success', 
          text: res.enquiry_created 
            ? `Simulated email processed: Enquiry #${res.enquiry_id} automatically created!` 
            : `Simulated email processed: Status set to ${res.status}.`
        });
        setActiveTab(res.enquiry_created ? 'all' : 'unclassified');
      } else {
        setFeedback({ type: 'error', text: 'Email was flagged as duplicate or could not be processed.' });
      }
      await loadData();
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message || 'Simulation failed.' });
    } finally {
      setIsSimulating(false);
    }
  };

  // Filter messages based on active tab and search
  const filteredMessages = messages.filter((m) => {
    if (activeTab === 'unclassified') {
      if (m.status !== 'UNCLASSIFIED') return false;
    }
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      m.subject.toLowerCase().includes(term) ||
      m.senderEmail.toLowerCase().includes(term) ||
      (m.senderName && m.senderName.toLowerCase().includes(term)) ||
      (m.bodyText && m.bodyText.toLowerCase().includes(term))
    );
  });

  const unclassifiedCount = messages.filter((m) => m.status === 'UNCLASSIFIED').length;

  return (
    <div className="space-y-6">
      {/* Top Banner & Gmail Connection Status */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#9E7D3B] font-medium mb-1">
            <Inbox size={14} />
            <span>Gmail Communications Hub</span>
          </div>
          <h1 className="font-serif text-2xl sm:text-3xl text-[#1F2421]">
            Agency Email Inbox and Intake
          </h1>
          <div className="flex flex-wrap items-center gap-3 text-xs text-[#736F68] mt-2">
            <span>Connected Inbox: <strong className="text-[#1F2421]">{status?.agencyEmail || 'saisubodh6@gmail.com'}</strong></span>
            <span>·</span>
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 ${status?.imapConfigured ? 'bg-[#2D5A3C]' : 'bg-[#C28E2E]'}`} />
              {status?.imapConfigured ? (
                <span className="text-[#2D5A3C] font-medium">IMAP SSL Active</span>
              ) : (
                <span className="text-[#8F592B]">Awaiting Gmail App Password in .env</span>
              )}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSyncMailbox}
            disabled={isSyncing}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] border border-[#1F2421] transition-colors disabled:opacity-60"
          >
            <RefreshCw size={13} className={isSyncing ? 'animate-spin text-[#D9C496]' : 'text-[#D9C496]'} />
            <span>{isSyncing ? 'Checking Gmail...' : 'Check Mailbox Now'}</span>
          </button>
        </div>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <div className={`p-4 border text-xs flex items-center justify-between ${
          feedback.type === 'success' 
            ? 'bg-[#F2F7F2] border-[#CDE3CD] text-[#245928]' 
            : 'bg-[#FBF1F0] border-[#E9C3C0] text-[#94352D]'
        }`}>
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
            <span>{feedback.text}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs font-bold uppercase ml-4">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center border-b border-[#E5E0D8] bg-[#FFFFFF] px-6 pt-3 gap-6 text-xs uppercase tracking-wider">
        <button
          onClick={() => setActiveTab('unclassified')}
          className={`pb-3 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'unclassified'
              ? 'border-[#1F2421] text-[#1F2421]'
              : 'border-transparent text-[#8C877D] hover:text-[#1F2421]'
          }`}
        >
          <span>Needs Review (Unclassified)</span>
          {unclassifiedCount > 0 && (
            <span className="px-1.5 py-0.2 bg-[#9E7D3B] text-[#FFFFFF] text-[10px] font-bold">
              {unclassifiedCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('all')}
          className={`pb-3 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'all'
              ? 'border-[#1F2421] text-[#1F2421]'
              : 'border-transparent text-[#8C877D] hover:text-[#1F2421]'
          }`}
        >
          <span>All Ingested Emails ({messages.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('simulate')}
          className={`pb-3 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'simulate'
              ? 'border-[#1F2421] text-[#1F2421]'
              : 'border-transparent text-[#8C877D] hover:text-[#1F2421]'
          }`}
        >
          <Sparkles size={13} className="text-[#9E7D3B]" />
          <span>Simulate Incoming Email (Dev Console)</span>
        </button>
      </div>

      {/* Tab 1 & 2: Email Listing */}
      {activeTab !== 'simulate' && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-4 flex items-center gap-3">
            <Search size={15} className="text-[#8C877D]" />
            <input
              type="text"
              placeholder="Search emails by sender, subject, or message content..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs bg-transparent focus:outline-none text-[#1F2421]"
            />
            {searchTerm && (
              <button onClick={() => setSearchTerm('')} className="text-xs text-[#8C877D] hover:text-[#1F2421]">
                Clear
              </button>
            )}
          </div>

          {/* Messages list */}
          {isLoading ? (
            <div className="p-12 text-center text-xs text-[#8C877D] bg-[#FFFFFF] border border-[#E5E0D8]">
              Loading emails...
            </div>
          ) : filteredMessages.length === 0 ? (
            <div className="p-12 text-center bg-[#FFFFFF] border border-[#E5E0D8] space-y-3">
              <Mail size={24} className="mx-auto text-[#9E7D3B]" />
              <div className="font-serif text-lg text-[#1F2421]">
                {activeTab === 'unclassified' ? 'No Unclassified Emails Pending Review' : 'No Emails Found'}
              </div>
              <p className="text-xs text-[#736F68] max-w-md mx-auto">
                {activeTab === 'unclassified' 
                  ? 'All incoming emails have been automatically matched to enquiries or reviewed by staff.' 
                  : 'No emails match your current search query.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredMessages.map((msg) => (
                <div
                  key={msg.id}
                  className="bg-[#FFFFFF] border border-[#E5E0D8] p-5 transition-shadow space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E5E0D8]">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-[#FAF8F5] border border-[#E5E0D8] flex items-center justify-center font-serif text-xs font-semibold text-[#9E7D3B]">
                        {(msg.senderName || msg.senderEmail).charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-[#1F2421]">
                          {msg.senderName || msg.senderEmail}
                        </div>
                        <div className="text-[11px] text-[#736F68]">
                          {msg.senderEmail}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold border ${
                        msg.status === 'ENQUIRY_CREATED'
                          ? 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9]'
                          : msg.status === 'ASSOCIATED'
                          ? 'bg-[#EBF2F7] text-[#295570] border-[#BCD4E6]'
                          : msg.status === 'IGNORED'
                          ? 'bg-[#F2EFE8] text-[#8C877D] border-[#D9D3C7]'
                          : 'bg-[#FDF6E2] text-[#8C6D1F] border-[#E8D49E]'
                      }`}>
                        {msg.status.replace(/_/g, ' ')}
                      </span>

                      <div className="text-[11px] text-[#8C877D] flex items-center gap-1">
                        <Clock size={12} />
                        <span>{new Date(msg.createdAt).toLocaleString('en-IN')}</span>
                      </div>
                    </div>
                  </div>

                  {/* Subject & Preview */}
                  <div>
                    <h3 className="font-serif text-sm font-semibold text-[#1F2421] mb-1">
                      {msg.subject}
                    </h3>
                    <p className="text-xs text-[#5C5850] leading-relaxed line-clamp-3 bg-[#FAF8F5] p-3 border border-[#E5E0D8]">
                      {msg.bodyText || '(No plain text content)'}
                    </p>
                  </div>

                  {/* Attachments */}
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-[10px] uppercase tracking-wider text-[#8C877D] flex items-center gap-1">
                        <Paperclip size={12} /> Attachments:
                      </span>
                      {msg.attachments.map((att) => (
                        <a
                          key={att.id}
                          href={att.downloadUrl || emailApi.getAttachmentUrl(msg.id, att.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] hover:bg-[#F2EFE8]"
                        >
                          <Paperclip size={11} className="text-[#9E7D3B]" />
                          <span>{att.originalFilename}</span>
                          <span className="text-[#8C877D] text-[10px]">({(att.fileSize / 1024).toFixed(1)} KB)</span>
                        </a>
                      ))}
                    </div>
                  )}

                  {/* Actions Bar */}
                  <div className="flex flex-wrap items-center justify-between pt-2 border-t border-[#E5E0D8] gap-3">
                    <div className="text-[11px] text-[#8C877D]">
                      {msg.enquiryId ? (
                        <span>Linked to Enquiry: <strong className="text-[#1F2421]">{msg.enquiryId}</strong></span>
                      ) : (
                        <span>Not associated with any wedding dossier</span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {msg.enquiryId ? (
                        <Link
                          to={`/enquiries/${msg.enquiryId}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1F2421] text-[#FAF8F5] text-[11px] uppercase tracking-wider font-semibold hover:bg-[#343733]"
                        >
                          <span>Open Enquiry Dossier</span>
                          <ArrowRight size={12} className="text-[#D9C496]" />
                        </Link>
                      ) : (
                        <>
                          <button
                            onClick={() => {
                              setConvertingMsg(msg);
                              setClientNameInput(msg.senderName || '');
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1F2421] text-[#FAF8F5] text-[11px] uppercase tracking-wider font-semibold hover:bg-[#343733]"
                          >
                            <Plus size={12} className="text-[#D9C496]" />
                            <span>Create Enquiry</span>
                          </button>

                          <button
                            onClick={() => {
                              setAssociatingMsg(msg);
                              setSelectedEnquiryId(enquiries[0]?.id || '');
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] text-[11px] uppercase tracking-wider hover:bg-[#F2EFE8]"
                          >
                            <Link2 size={12} className="text-[#9E7D3B]" />
                            <span>Associate with Dossier</span>
                          </button>

                          {msg.status !== 'IGNORED' && (
                            <button
                              onClick={() => handleIgnore(msg.id)}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] uppercase tracking-wider text-[#94352D] hover:bg-[#FBF1F0]"
                            >
                              <Trash2 size={12} />
                              <span>Ignore</span>
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Simulation Console (For automated testing and demo) */}
      {activeTab === 'simulate' && (
        <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
          <div className="pb-4 border-b border-[#E5E0D8]">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#9E7D3B] font-medium mb-1">
              <Sparkles size={14} />
              <span>Developer and Testing Console</span>
            </div>
            <h2 className="font-serif text-2xl text-[#1F2421]">
              Simulate Incoming Client Email
            </h2>
            <p className="text-xs text-[#736F68] mt-1">
              Simulates receiving an email into <strong className="text-[#1F2421]">saisubodh6@gmail.com</strong>.
              This executes the exact classification, keyword detection, deduplication, and attachment handling logic
              without requiring live Gmail IMAP credentials.
            </p>
          </div>

          <form onSubmit={handleSimulateSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Sender Client Name *</label>
                <input
                  type="text"
                  required
                  value={simSenderName}
                  onChange={(e) => setSimSenderName(e.target.value)}
                  className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>

              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Sender Email Address *</label>
                <input
                  type="email"
                  required
                  value={simSenderEmail}
                  onChange={(e) => setSimSenderEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Email Subject *</label>
              <input
                type="text"
                required
                value={simSubject}
                onChange={(e) => setSimSubject(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Email Body Message *</label>
              <textarea
                rows={4}
                required
                value={simBody}
                onChange={(e) => setSimBody(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase text-[#8C877D] mb-1">
                Attach File (e.g. Completed Registration PDF or Invitation Letter)
              </label>
              <input
                type="file"
                onChange={(e) => setSimFile(e.target.files ? e.target.files[0] : null)}
                className="text-xs file:mr-2 file:py-1 file:px-3 file:border file:border-[#E5E0D8] file:text-xs file:bg-[#FAF8F5]"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSimulating}
                className="flex items-center gap-2 px-6 py-2.5 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold hover:bg-[#343733] disabled:opacity-60"
              >
                <Send size={13} className="text-[#D9C496]" />
                <span>{isSimulating ? 'Injecting Simulated Email...' : 'Inject Incoming Email'}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Convert to Enquiry Modal */}
      {convertingMsg && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border-2 border-[#1F2421] p-6 sm:p-8 max-w-md w-full space-y-4">
            <div className="pb-3 border-b border-[#E5E0D8]">
              <h3 className="font-serif text-xl text-[#1F2421]">Convert Email to Wedding Enquiry</h3>
              <p className="text-xs text-[#736F68] mt-1">
                Creates a new client enquiry dossier pre-filled with this client's email and message.
              </p>
            </div>

            <form onSubmit={handleConvertToEnquiry} className="space-y-4 text-xs">
              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Client / Couple Name *</label>
                <input
                  type="text"
                  required
                  value={clientNameInput}
                  onChange={(e) => setClientNameInput(e.target.value)}
                  placeholder="e.g. Maharani Gayatri Rao"
                  className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                />
              </div>

              <div>
                <span className="block text-[10px] uppercase text-[#8C877D] mb-1">From:</span>
                <div className="font-mono text-xs text-[#1F2421] bg-[#FAF8F5] p-2 border border-[#E5E0D8]">
                  {convertingMsg.senderEmail}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setConvertingMsg(null)}
                  className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] text-xs uppercase"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isConverting}
                  className="px-6 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold disabled:opacity-50"
                >
                  {isConverting ? 'Creating...' : 'Create Enquiry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Associate Modal */}
      {associatingMsg && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border-2 border-[#1F2421] p-6 sm:p-8 max-w-md w-full space-y-4">
            <div className="pb-3 border-b border-[#E5E0D8]">
              <h3 className="font-serif text-xl text-[#1F2421]">Associate Email with Dossier</h3>
              <p className="text-xs text-[#736F68] mt-1">
                Link this client message to an existing wedding planning dossier.
              </p>
            </div>

            <form onSubmit={handleAssociate} className="space-y-4 text-xs">
              <div>
                <label className="block text-[10px] uppercase text-[#8C877D] mb-1">Select Wedding Enquiry *</label>
                <select
                  value={selectedEnquiryId}
                  onChange={(e) => setSelectedEnquiryId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
                >
                  {enquiries.map((enq) => (
                    <option key={enq.id} value={enq.id}>
                      {enq.id} — {enq.clientName} ({enq.status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E5E0D8]">
                <button
                  type="button"
                  onClick={() => setAssociatingMsg(null)}
                  className="px-4 py-2 bg-[#FAF8F5] border border-[#E5E0D8] text-[#5C5850] text-xs uppercase"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAssociating}
                  className="px-6 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-wider font-semibold disabled:opacity-50"
                >
                  {isAssociating ? 'Associating...' : 'Confirm Association'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
