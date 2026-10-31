import React, { useState, useEffect } from 'react';
import { useClients } from '../context/ClientContext';
import { registrationApi } from '../services/api';
import {
  Building,
  MapPin,
  Shield,
  Check,
  FileSpreadsheet,
  ExternalLink,
  RefreshCw,
  UploadCloud,
  Code2,
  CheckCircle2,
  AlertCircle,
  Copy,
} from 'lucide-react';

const GOOGLE_APPS_SCRIPT_TEMPLATE = `function onFormSubmit(e) {
  // Replace with your active backend URL or ngrok/toggled domain
  var backendWebhookUrl = "http://localhost:8000/api/v1/registrations/google-forms-webhook";

  var itemResponses = e.response.getItemResponses();
  var payload = {
    response_id: e.response.getId(),
    timestamp: e.response.getTimestamp().toISOString()
  };

  for (var i = 0; i < itemResponses.length; i++) {
    var itemResponse = itemResponses[i];
    var title = itemResponse.getItem().getTitle();
    var response = itemResponse.getResponse();
    payload[title] = Array.isArray(response) ? response.join(", ") : response;
  }

  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  UrlFetchApp.fetch(backendWebhookUrl, options);
}`;

export const SettingsPage: React.FC = () => {
  const { currentUser } = useClients();

  // Google Forms & Sheets State
  const [formUrl, setFormUrl] = useState('');
  const [sheetId, setSheetId] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [copiedScript, setCopiedScript] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const config = await registrationApi.getConfig();
      setFormUrl(config.googleFormsRegistrationUrl || '');
      setSheetId(config.googleSheetId || '');
      setWebhookUrl(config.webhookUrl || '');
    } catch (err: any) {
      console.error('Failed to load Google Forms config:', err);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      const updated = await registrationApi.updateConfig({
        googleFormsRegistrationUrl: formUrl,
        googleSheetId: sheetId || undefined,
      });
      setFormUrl(updated.googleFormsRegistrationUrl);
      setSheetId(updated.googleSheetId || '');
      setFeedback({ type: 'success', message: 'Google Forms configuration saved successfully.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to update configuration.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSyncSheet = async () => {
    setIsSyncing(true);
    setFeedback(null);
    try {
      const res = await registrationApi.syncGoogleSheet(sheetId || undefined);
      if (res.success) {
        setFeedback({
          type: 'success',
          message: res.message || 'Google Sheet synced successfully.',
        });
      } else {
        setFeedback({
          type: 'error',
          message: res.message || 'Sync failed. Please check sheet sharing permissions.',
        });
      }
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Network error syncing Google Sheet.',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setFeedback(null);
    try {
      const res = await registrationApi.importCsv(file);
      setFeedback({
        type: 'success',
        message: res.message || `Imported ${res.stats?.imported} rows from ${file.name}.`,
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to parse and import CSV file.',
      });
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const copyScriptToClipboard = () => {
    navigator.clipboard.writeText(GOOGLE_APPS_SCRIPT_TEMPLATE);
    setCopiedScript(true);
    setTimeout(() => setCopiedScript(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-6 border-b border-[#E5E0D8]">
        <div className="text-[10px] tracking-[0.2em] uppercase text-[#9E7D3B] font-medium mb-1">
          Configuration & Preferences
        </div>
        <h1 className="font-serif text-3xl text-[#1F2421]">Agency System Settings</h1>
        <p className="text-xs text-[#736F68] mt-1">
          Operating parameters for The Royal Knot luxury wedding planning operations.
        </p>
      </div>

      {/* Google Forms & Google Sheets Integration Card */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E5E0D8] gap-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet size={18} className="text-[#9E7D3B]" />
            <div>
              <h2 className="font-serif text-xl text-[#1F2421]">Client Registration via Google Forms</h2>
              <p className="text-[11px] text-[#736F68]">
                Configure the Google Form registration link sent in welcome emails and synchronize client submissions into PostgreSQL.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowScriptModal(!showScriptModal)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#9E7D3B] border border-[#9E7D3B] hover:bg-[#FAF8F5] transition-colors self-start sm:self-auto"
          >
            <Code2 size={13} />
            <span>Webhook Script Guide</span>
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-3.5 text-xs flex items-center gap-2 border ${
              feedback.type === 'success'
                ? 'bg-[#EBF3ED] text-[#2D5A3C] border-[#C3D9C9]'
                : 'bg-[#FDF2F2] text-[#9E2B2B] border-[#F2C2C2]'
            }`}
          >
            {feedback.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
            <span>{feedback.message}</span>
          </div>
        )}

        <form onSubmit={handleSaveConfig} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Google Forms Registration URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                required
                value={formUrl}
                onChange={(e) => setFormUrl(e.target.value)}
                placeholder="https://docs.google.com/forms/d/e/.../viewform"
                className="flex-1 px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              />
              {formUrl && (
                <a
                  href={formUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] hover:border-[#9E7D3B] transition-colors"
                  title="Open Form in new tab"
                >
                  <ExternalLink size={13} />
                  <span>Preview</span>
                </a>
              )}
            </div>
            <p className="text-[11px] text-[#8C877D] mt-1">
              Included in the automated luxury welcome emails sent to potential clients who contact our agency.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                Connected Google Sheet ID (Optional)
              </label>
              <input
                type="text"
                value={sheetId}
                onChange={(e) => setSheetId(e.target.value)}
                placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421] focus:outline-none focus:border-[#9E7D3B]"
              />
              <p className="text-[11px] text-[#8C877D] mt-1">
                The ID extracted from your responses spreadsheet URL: docs.google.com/spreadsheets/d/<strong>ID</strong>/edit
              </p>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
                FastAPI Webhook Push Endpoint
              </label>
              <input
                type="text"
                readOnly
                value={webhookUrl || 'http://localhost:8000/api/v1/registrations/google-forms-webhook'}
                className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#736F68] font-mono cursor-not-allowed"
              />
              <p className="text-[11px] text-[#8C877D] mt-1">
                Google Apps Script onFormSubmit(e) sends responses directly to this endpoint.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between pt-4 border-t border-[#E5E0D8] gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2 bg-[#1F2421] text-[#FAF8F5] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#9E7D3B] transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleSyncSheet}
                disabled={isSyncing || !sheetId}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-[#E5E0D8] text-xs text-[#1F2421] hover:border-[#9E7D3B] bg-[#FAF8F5] transition-colors disabled:opacity-40"
              >
                <RefreshCw size={13} className={isSyncing ? 'animate-spin' : ''} />
                <span>{isSyncing ? 'Syncing Sheet...' : 'Sync with Google Sheet'}</span>
              </button>

              <label className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-[#E5E0D8] text-xs text-[#1F2421] hover:border-[#9E7D3B] bg-[#FAF8F5] transition-colors cursor-pointer">
                <UploadCloud size={13} />
                <span>{isUploading ? 'Importing CSV...' : 'Import Forms CSV'}</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleCsvUpload}
                  className="hidden"
                  disabled={isUploading}
                />
              </label>
            </div>
          </div>
        </form>

        {/* Apps Script Guide Modal / Accordion */}
        {showScriptModal && (
          <div className="mt-4 p-5 bg-[#FAF8F5] border border-[#E5E0D8] space-y-4 text-xs text-[#4A4640]">
            <div className="flex items-center justify-between pb-2 border-b border-[#E5E0D8]">
              <span className="font-serif text-sm font-semibold text-[#1F2421]">
                Google Apps Script Real-Time Webhook Setup
              </span>
              <button
                type="button"
                onClick={copyScriptToClipboard}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] border border-[#9E7D3B] text-[#9E7D3B] hover:bg-white"
              >
                {copiedScript ? <Check size={12} /> : <Copy size={12} />}
                <span>{copiedScript ? 'Copied!' : 'Copy Script'}</span>
              </button>
            </div>

            <ol className="list-decimal list-inside space-y-1.5 text-[11px] text-[#736F68] leading-relaxed">
              <li>Open your Google Form in Google Drive.</li>
              <li>Click the three dots menu (top right) and select <strong>Script editor</strong>.</li>
              <li>Paste the code snippet below into <code>Code.gs</code>.</li>
              <li>In the left sidebar, click <strong>Triggers (alarm clock icon)</strong> &gt; <strong>Add Trigger</strong>.</li>
              <li>Select function: <code>onFormSubmit</code>, Event source: <code>From form</code>, Event type: <code>On form submit</code>.</li>
              <li>Click <strong>Save</strong> and authorize Google permissions. Submissions will now instantly flow into your PostgreSQL database!</li>
            </ol>

            <pre className="p-3 bg-[#1F2421] text-[#FAF8F5] font-mono text-[10px] leading-relaxed overflow-x-auto max-h-48 border border-[#1F2421]">
              {GOOGLE_APPS_SCRIPT_TEMPLATE}
            </pre>
          </div>
        )}
      </div>

      {/* Agency Identity */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
          <Building size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">Agency Profile</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Agency Name
            </label>
            <input
              type="text"
              readOnly
              value="The Royal Knot — Luxury Wedding Planners"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Operating Headquarters
            </label>
            <input
              type="text"
              readOnly
              value="Jaipur & Udaipur, Rajasthan, India"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Current Logged-in Staff
            </label>
            <input
              type="text"
              readOnly
              value={`${currentUser.name} (${currentUser.role})`}
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#736F68] font-medium mb-1.5">
              Official Contact Email
            </label>
            <input
              type="text"
              readOnly
              value="saisubodh6@gmail.com"
              className="w-full px-3.5 py-2.5 text-xs bg-[#FAF8F5] border border-[#E5E0D8] text-[#1F2421]"
            />
          </div>
        </div>
      </div>

      {/* Flagship Hubs */}
      <div className="bg-[#FFFFFF] border border-[#E5E0D8] p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-[#E5E0D8]">
          <MapPin size={16} className="text-[#9E7D3B]" />
          <h2 className="font-serif text-xl text-[#1F2421]">Regional Operations Hubs</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5]">
            <div className="flex items-center justify-between mb-2">
              <span className="font-serif text-base font-semibold text-[#1F2421]">Jaipur Flagship Hub</span>
              <span className="text-[10px] text-[#2D5A3C] bg-[#EBF3ED] px-2 py-0.5 border border-[#C3D9C9] font-medium">Active</span>
            </div>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Rambagh Palace Circle, C-Scheme, Jaipur, Rajasthan 302001
            </p>
          </div>

          <div className="p-4 border border-[#E5E0D8] bg-[#FAF8F5]">
            <div className="flex items-center justify-between mb-2">
              <span className="font-serif text-base font-semibold text-[#1F2421]">Udaipur Lake Hub</span>
              <span className="text-[10px] text-[#2D5A3C] bg-[#EBF3ED] px-2 py-0.5 border border-[#C3D9C9] font-medium">Active</span>
            </div>
            <p className="text-[11px] text-[#736F68] leading-relaxed">
              Pichola Promenade, Haridas Ji Ki Magri, Udaipur, Rajasthan 313001
            </p>
          </div>
        </div>
      </div>

      {/* System Status info */}
      <div className="p-4 bg-[#FFFFFF] border border-[#E5E0D8] flex items-center justify-between text-xs text-[#736F68]">
        <div className="flex items-center gap-2">
          <Shield size={14} className="text-[#9E7D3B]" />
          <span>System Environment: Full-Stack Production Architecture</span>
        </div>
        <div className="flex items-center gap-1 text-[#2D5A3C]">
          <Check size={14} />
          <span className="font-medium">PostgreSQL & Google Forms Active</span>
        </div>
      </div>
    </div>
  );
};
