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
  onViewDoc: (doc: UploadedDocument) => void;
  uploadingFiles: Map<string, number>;
  onUploadStart: (filename: string) => void;
  onUploadProgress: (filename: string, progress: number) => void;
};

export const Sidebar: React.FC<Props> = ({
  isOpen,
  onToggle,
  uploadedDocs,
  onNewChat,
  onDeleteDoc,
  onUploaded,
  onViewDoc,
  uploadingFiles,
  onUploadStart,
  onUploadProgress,
}) => {
  const [searchQuery, setSearchQuery] = React.useState("");

  const filteredDocs = uploadedDocs.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

        <PdfUpload 
          onUploaded={onUploaded}
          onUploadStart={onUploadStart}
          onUploadProgress={onUploadProgress}
          variant="sidebar" 
        />
      </div>

      {uploadedDocs.length > 0 && (
        <div className="px-3 pb-3">
          <div className="border-t border-slate-800 pt-3">
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
              {uploadedDocs.slice(0, 3).map((doc) => (
                <button
                  key={doc.documentId}
                  onClick={() => onViewDoc(doc)}
                  className="flex-shrink-0 flex items-center gap-2 px-2.5 py-2 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700 hover:border-indigo-500/50 transition-all"
                >
                  <svg className="w-3.5 h-3.5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-xs font-medium text-slate-200 max-w-[100px] truncate">
                    {doc.filename}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="px-3 pb-3">
        <div className="relative">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 pl-9 bg-slate-800 border border-slate-700 rounded-lg text-sm placeholder:text-slate-500 focus:outline-none focus:border-slate-600 transition-colors"
          />
          <svg className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="space-y-2">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Uploaded PDFs
            </h3>
            <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
              {filteredDocs.length}
            </span>
          </div>
          
          {/* Show uploading files */}
          {Array.from(uploadingFiles.entries()).map(([filename, progress]) => (
            <div
              key={filename}
              className="flex items-start gap-2 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/30 animate-pulse"
            >
              <div className="flex-shrink-0 mt-0.5">
                <svg className="w-5 h-5 text-indigo-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-100 truncate" title={filename}>
                  {filename}
                </p>
                <div className="mt-1.5">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-500 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-indigo-400 font-medium min-w-[60px]">
                      {progress === 100 ? 'Processing...' : `${progress}%`}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {uploadedDocs.length === 0 && uploadingFiles.size === 0 ? (
            <div className="text-center py-8 px-4">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800 flex items-center justify-center">
                <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-xs text-slate-500">No documents uploaded yet</p>
              <p className="text-xs text-slate-600 mt-1">Upload PDFs to get started</p>
            </div>
          ) : filteredDocs.length === 0 && uploadingFiles.size === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-4 text-center">
              No documents match your search
            </div>
          ) : (
            <div className="space-y-1">
              {filteredDocs.map((doc) => (
                <div
                  key={doc.documentId}
                  className="group flex items-start gap-2 p-3 rounded-lg hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all cursor-pointer"
                  onClick={() => onViewDoc(doc)}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {doc.uploadedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewDoc(doc);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-slate-700 rounded transition-all"
                      aria-label="View document"
                    >
                      <svg className="w-4 h-4 text-slate-400 hover:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteDoc(doc.documentId);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-slate-700 rounded transition-all"
                      aria-label="Delete document"
                    >
                      <svg className="w-4 h-4 text-slate-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
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
