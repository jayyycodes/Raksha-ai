'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { UploadItem } from '@/lib/api/types';
import { fetchUploads, uploadDataFile, deleteUpload } from '@/lib/api/client';
import { formatISTDate } from '@/lib/utils';

export default function UploadPage() {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [selectedUpload, setSelectedUpload] = useState<UploadItem | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState<boolean>(false);

  const loadUploads = async () => {
    setLoading(true);
    const res = await fetchUploads();
    if (res && res.items) {
      setUploads(res.items);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadUploads();
  }, []);

  const handleFileSubmit = async (file: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setUploading(true);

    const res = await uploadDataFile(file);
    setUploading(false);

    if (!res.success) {
      setErrorMsg(res.message || 'File upload failed');
    } else {
      setSuccessMsg(`File "${file.name}" safely parsed and stored in workspace sandbox.`);
      if (res.upload) {
        setSelectedUpload(res.upload);
      }
      loadUploads();
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      handleFileSubmit(file);
    }
  };

  const handleDelete = async (id: number, filename: string) => {
    if (!confirm(`Are you sure you want to permanently purge "${filename}" and its sandboxed data?`)) {
      return;
    }
    const ok = await deleteUpload(id);
    if (ok) {
      setSuccessMsg(`File "${filename}" purged from sandbox.`);
      if (selectedUpload?.id === id) setSelectedUpload(null);
      loadUploads();
    } else {
      setErrorMsg('Failed to delete upload record.');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-accent-saffron/15 text-accent-saffron border border-accent-saffron/30 font-bold">
              RESTRICTED // WORKSPACE ISOLATED
            </span>
            <span className="text-[10px] text-text-muted font-mono">BYOD INGESTION ENGINE</span>
          </div>
          <h1 className="text-2xl font-serif font-black text-text-primary tracking-tight">
            Bring Your Own Data · Sandboxed Upload
          </h1>
          <p className="text-xs text-text-secondary mt-1 max-w-3xl leading-relaxed">
            Upload custom field logs, intelligence CSV feeds, wire transcripts, and surveillance reports.
            All files undergo magic byte verification, strict 15MB/50-page limits, and are isolated to your workspace sandbox with source tagging.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/cases"
            className="px-3 py-1.5 rounded text-xs font-semibold border border-border bg-card hover:bg-subtle-fill text-text-primary transition-colors"
          >
            Open Cases 💼
          </Link>
          <Link
            href="/audit"
            className="px-3 py-1.5 rounded text-xs font-semibold border border-border bg-card hover:bg-subtle-fill text-text-primary transition-colors"
          >
            Audit Log 🛡️
          </Link>
        </div>
      </div>

      {/* Security & Sandboxing Architecture Guarantee */}
      <div className="p-4 rounded-lg bg-surface-raised border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">🛡️</span>
          <div>
            <h4 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              Air-Gapped Sandbox & Provenance Safeguards
            </h4>
            <div className="text-[11px] text-text-secondary mt-1 flex flex-wrap gap-x-4 gap-y-1">
              <span>✓ 15MB Size Constraint</span>
              <span>✓ 50-Page PDF Anti-DoS Limit</span>
              <span>✓ Executable & Script Prohibition (ELF/PE/XSS)</span>
              <span>✓ Private Workspace Tagging (<code className="text-accent-saffron">source_type=&apos;user_upload&apos;</code>)</span>
              <span>✓ Excluded from public threat scoring</span>
            </div>
          </div>
        </div>
        <div className="text-right text-[10px] font-mono text-text-muted shrink-0">
          Storage: <code className="text-accent-saffron">data/uploads/sandboxed/</code>
        </div>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-3 bg-red-950/30 border border-red-800 text-red-300 text-xs rounded-md flex items-center justify-between">
          <span>⚠️ {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-red-400 font-bold hover:underline">
            ✕
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-3 bg-emerald-950/30 border border-emerald-800 text-emerald-300 text-xs rounded-md flex items-center justify-between">
          <span>✅ {successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 font-bold hover:underline">
            ✕
          </button>
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          dragOver
            ? 'border-accent-saffron bg-accent-saffron/5 shadow-inner'
            : 'border-border bg-card/60 hover:bg-subtle-fill hover:border-text-muted'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt,.pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSubmit(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center gap-2">
          <div className="w-12 h-12 rounded-full bg-subtle-fill flex items-center justify-center text-2xl">
            {uploading ? '⏳' : '📥'}
          </div>
          <h3 className="text-sm font-bold text-text-primary">
            {uploading ? 'Validating & Parsing Document...' : 'Drag & Drop File Here, or Click to Browse'}
          </h3>
          <p className="text-xs text-text-secondary max-w-md">
            Supports structured intelligence feeds in <strong>.CSV</strong>, tactical wire transcripts in <strong>.TXT</strong>, or dossier reports in <strong>.PDF</strong> (up to 50 pages).
          </p>
          <div className="mt-2 flex gap-2">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
              .CSV
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
              .TXT
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
              .PDF
            </span>
          </div>
        </div>
      </div>

      {/* Parsing Summary Preview (if an upload was just processed or selected) */}
      {selectedUpload && (
        <div className="p-5 rounded-lg bg-card border border-accent-saffron/40 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-3">
              <span className="text-xl">
                {selectedUpload.mime_type.includes('pdf') ? '📄' : selectedUpload.mime_type.includes('csv') ? '📊' : '📝'}
              </span>
              <div>
                <h3 className="text-sm font-bold text-text-primary font-mono">{selectedUpload.filename}</h3>
                <span className="text-[11px] text-text-muted">
                  SHA-256: <code className="text-accent-saffron">{selectedUpload.file_hash.substring(0, 24)}...</code> · {(selectedUpload.file_size / 1024).toFixed(1)} KB
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedUpload(null)}
              className="text-xs text-text-muted hover:text-text-primary"
            >
              Close Preview ✕
            </button>
          </div>

          {/* Structured Details */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-2.5 rounded bg-surface-raised border border-border">
              <span className="text-[10px] text-text-muted uppercase block">Format</span>
              <span className="font-bold text-text-primary uppercase">{selectedUpload.parse_summary.format || 'Unknown'}</span>
            </div>
            <div className="p-2.5 rounded bg-surface-raised border border-border">
              <span className="text-[10px] text-text-muted uppercase block">Extracted Count</span>
              <span className="font-bold text-accent-saffron">
                {selectedUpload.parse_summary.row_count !== undefined
                  ? `${selectedUpload.parse_summary.row_count} rows`
                  : selectedUpload.parse_summary.page_count !== undefined
                  ? `${selectedUpload.parse_summary.page_count} pages`
                  : `${selectedUpload.parse_summary.word_count || 0} words`}
              </span>
            </div>
            <div className="p-2.5 rounded bg-surface-raised border border-border">
              <span className="text-[10px] text-text-muted uppercase block">Status</span>
              <span className="font-bold text-emerald-400 capitalize">{selectedUpload.status}</span>
            </div>
            <div className="p-2.5 rounded bg-surface-raised border border-border">
              <span className="text-[10px] text-text-muted uppercase block">Uploaded By</span>
              <span className="font-bold text-text-secondary truncate block">{selectedUpload.uploader_email}</span>
            </div>
          </div>

          {/* Sample CSV Data or Text Preview */}
          {selectedUpload.parse_summary.sample && selectedUpload.parse_summary.sample.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                Extracted CSV Rows Sample (First 5 Rows)
              </h4>
              <div className="overflow-x-auto rounded border border-border">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-subtle-fill text-text-muted">
                    <tr>
                      {selectedUpload.parse_summary.columns?.map((col) => (
                        <th key={col} className="p-2 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60 bg-card">
                    {selectedUpload.parse_summary.sample.map((row, idx) => (
                      <tr key={idx} className="hover:bg-subtle-fill/40">
                        {selectedUpload.parse_summary.columns?.map((col) => (
                          <td key={col} className="p-2 text-text-secondary max-w-xs truncate">
                            {row[col] || '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedUpload.parse_summary.preview_snippet && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                Document Text Excerpt
              </h4>
              <pre className="p-3 bg-surface-raised border border-border rounded text-xs font-mono text-text-secondary whitespace-pre-wrap max-h-48 overflow-y-auto">
                {selectedUpload.parse_summary.preview_snippet}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Ingested Files Inventory */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-serif font-bold text-text-primary tracking-tight uppercase">
            Workspace Ingestion Inventory ({uploads.length})
          </h2>
          <button
            onClick={loadUploads}
            className="text-xs font-mono text-accent-saffron hover:underline"
          >
            Refresh List ↻
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-text-muted font-mono">
            Loading sandboxed repository...
          </div>
        ) : uploads.length === 0 ? (
          <div className="p-8 text-center bg-card border border-border rounded-lg text-xs text-text-muted">
            No custom files uploaded in this workspace yet. Use the upload box above to ingest OSINT feeds.
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-card overflow-x-auto shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-subtle-fill border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="py-2.5 px-4">Filename</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Size</th>
                  <th className="py-2.5 px-3">Summary</th>
                  <th className="py-2.5 px-3">Uploader</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {uploads.map((item) => (
                  <tr key={item.id} className="hover:bg-subtle-fill/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-text-primary">
                      <button
                        onClick={() => setSelectedUpload(item)}
                        className="hover:text-accent-saffron hover:underline text-left"
                      >
                        {item.filename}
                      </button>
                      <div className="text-[10px] text-text-muted font-normal">
                        Hash: {item.file_hash.substring(0, 12)}...
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary uppercase">
                        {item.mime_type.split('/')[1] || item.mime_type}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-text-secondary">
                      {(item.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-3 text-text-secondary">
                      {item.parse_summary.row_count !== undefined
                        ? `${item.parse_summary.row_count} rows`
                        : item.parse_summary.page_count !== undefined
                        ? `${item.parse_summary.page_count} pages`
                        : item.parse_summary.word_count !== undefined
                        ? `${item.parse_summary.word_count} words`
                        : 'Parsed'}
                    </td>
                    <td className="py-3 px-3 text-text-secondary truncate max-w-[140px]">
                      {item.uploader_email}
                    </td>
                    <td className="py-3 px-3 text-text-muted font-mono whitespace-nowrap">
                      {formatISTDate(item.created_at)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                      <button
                        onClick={() => setSelectedUpload(item)}
                        className="px-2 py-1 text-[11px] rounded bg-subtle-fill hover:bg-border text-text-primary"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => handleDelete(item.id, item.filename)}
                        className="px-2 py-1 text-[11px] rounded bg-red-950/20 hover:bg-red-950/40 text-red-400 border border-red-900/30"
                      >
                        Purge
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
