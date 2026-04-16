import React from "react";

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  uploadedDocs: UploadedDocument[];
  onSelectDocument: (doc: UploadedDocument) => void;
  onUploadNew: () => void;
};

export const ReadModeSelector: React.FC<Props> = ({
  isOpen,
  onClose,
  uploadedDocs,
  onSelectDocument,
  onUploadNew,
}) => {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [loadingDocId, setLoadingDocId] = React.useState<string | null>(null);

  if (!isOpen) return null;

  const filteredDocs = uploadedDocs.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-2xl mx-4 bg-[#111111] rounded-2xl shadow-2xl border border-white/10 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Open in Read Mode</h2>
              <p className="text-xs text-slate-400">Select a PDF to read and chat with AI assistance</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Search and Upload */}
        <div className="px-6 py-4 border-b border-white/10 space-y-3">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>

          <button
            onClick={() => {
              onUploadNew();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-500 hover:bg-indigo-600 rounded-lg text-sm font-medium text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            Upload New PDF
          </button>
        </div>

        {/* Document List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredDocs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <svg className="w-16 h-16 text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-slate-400 mb-2">
                {searchQuery ? "No documents found" : "No documents uploaded yet"}
              </p>
              <p className="text-xs text-slate-500">
                {searchQuery ? "Try a different search term" : "Upload a PDF to get started"}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {filteredDocs.map((doc) => (
                <button
                  key={doc.documentId}
                  onClick={async () => {
                    setLoadingDocId(doc.documentId);
                    try {
                      await onSelectDocument(doc);
                      onClose();
                    } finally {
                      setLoadingDocId(null);
                    }
                  }}
                  disabled={loadingDocId === doc.documentId}
                  className="w-full flex items-center gap-4 px-6 py-4 hover:bg-slate-800/50 transition-colors text-left group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
                    {loadingDocId === doc.documentId ? (
                      <svg className="w-5 h-5 text-red-400 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate group-hover:text-slate-100">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-slate-500">
                      {loadingDocId === doc.documentId ? "Loading..." : `Uploaded ${doc.uploadedAt.toLocaleDateString()}`}
                    </p>
                  </div>
                  <svg
                    className="w-5 h-5 text-slate-600 group-hover:text-indigo-400 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
