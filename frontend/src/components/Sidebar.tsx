import React from "react";
import { PdfUpload } from "./PdfUpload";

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
};

type Props = {
  isOpen: boolean;
  onToggle: () => void;
  uploadedDocs: UploadedDocument[];
  onNewChat: () => void;
  onDeleteDoc: (documentId: string) => void;
  onUploaded: (info: { documentId: string; filename: string }) => void;
};

export const Sidebar: React.FC<Props> = ({
  isOpen,
  onToggle,
  uploadedDocs,
  onNewChat,
  onDeleteDoc,
  onUploaded,
}) => {
  if (!isOpen) return null;

  return (
    <div className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h2 className="font-semibold text-slate-100">Documents</h2>
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
          aria-label="Close sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-3 space-y-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-slate-700 hover:bg-slate-800 transition-colors text-sm font-medium"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>

        <PdfUpload onUploaded={onUploaded} variant="sidebar" />
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2">
            Uploaded PDFs ({uploadedDocs.length})
          </h3>
          {uploadedDocs.length === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-4 text-center">
              No documents uploaded yet
            </div>
          ) : (
            <div className="space-y-1">
              {uploadedDocs.map((doc) => (
                <div
                  key={doc.documentId}
                  className="group flex items-start gap-2 p-2 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {doc.uploadedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <button
                    onClick={() => onDeleteDoc(doc.documentId)}
                    className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-700 rounded transition-all"
                    aria-label="Delete document"
                  >
                    <svg className="w-3.5 h-3.5 text-slate-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-3 border-t border-slate-800">
        <div className="text-xs text-slate-500 space-y-1">
          <div className="flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>RAG-powered PDF chat</span>
          </div>
        </div>
      </div>
    </div>
  );
};
