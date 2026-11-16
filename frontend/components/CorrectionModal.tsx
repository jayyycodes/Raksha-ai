'use client';

import React, { useState } from 'react';
import { submitCorrectionRequest } from '@/lib/api/client';

interface CorrectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: 'entity' | 'article' | 'event' | 'threat_score';
  targetId: string;
  targetTitle?: string;
}

export const CorrectionModal: React.FC<CorrectionModalProps> = ({
  isOpen,
  onClose,
  targetType,
  targetId,
  targetTitle,
}) => {
  const [email, setEmail] = useState('');
  const [claimDetails, setClaimDetails] = useState('');
  const [evidence, setEvidence] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successTicket, setSuccessTicket] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !claimDetails.trim()) {
      setErrorMsg('Requester email and detailed claim are required.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    const res = await submitCorrectionRequest({
      target_type: targetType,
      target_id: targetId,
      requester_email: email.trim(),
      claim_details: claimDetails.trim(),
      supporting_evidence: evidence.trim() || undefined,
    });

    setSubmitting(false);

    if (!res.success) {
      setErrorMsg(res.message || 'Failed to submit correction request.');
    } else {
      setSuccessTicket(res.id || 1);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-blue-950/40 text-blue-400 border border-blue-800/50">
                DPDP ACT · GOVERNANCE
              </span>
            </div>
            <h3 className="text-base font-serif font-bold text-text-primary mt-1">
              Submit Intelligence Correction / Takedown Request
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary p-1 text-sm"
          >
            ✕
          </button>
        </div>

        {successTicket ? (
          <div className="py-6 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-950/40 border border-emerald-800 text-emerald-400 mx-auto flex items-center justify-center text-xl font-bold">
              ✓
            </div>
            <h4 className="text-sm font-bold text-text-primary">
              Correction Ticket #{successTicket} Lodged
            </h4>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              Your inquiry has been logged into the immutable audit system for oversight review pursuant to Indian DPDP Act standards.
            </p>
            <button
              onClick={() => {
                setSuccessTicket(null);
                onClose();
              }}
              className="mt-2 px-4 py-1.5 rounded text-xs font-semibold bg-accent-saffron text-slate-900"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {errorMsg && (
              <div className="p-2.5 rounded bg-red-950/30 border border-red-800 text-red-300">
                ⚠️ {errorMsg}
              </div>
            )}

            <div className="p-2.5 rounded bg-surface-raised border border-border">
              <span className="text-[10px] uppercase font-bold text-text-muted block">
                Target Record
              </span>
              <div className="font-mono text-text-primary mt-0.5">
                <span className="uppercase text-accent-saffron font-bold">[{targetType}]</span>{' '}
                {targetTitle || `ID #${targetId}`}
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                Requester Email *
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@domain.in or citizen@gov.in"
                className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-navy"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                Claim Details & Grounds *
              </label>
              <textarea
                required
                rows={3}
                value={claimDetails}
                onChange={(e) => setClaimDetails(e.target.value)}
                placeholder="Describe why this extraction, entity profile, or event requires correction or retraction..."
                className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-navy"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                Supporting Evidence / Reference Links (Optional)
              </label>
              <textarea
                rows={2}
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
                placeholder="Official press release URL, gazette notification, or retraction wire link..."
                className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-navy"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded border border-border text-text-secondary hover:bg-subtle-fill"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-1.5 rounded bg-primary-navy text-accent-saffron font-bold hover:bg-primary-navy/90 disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Lodge Request'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
