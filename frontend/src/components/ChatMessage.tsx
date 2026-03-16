import React from "react";

export type ChatRole = "user" | "assistant";

type Reference = {
  documentId: string;
  pageNumber: number;
  documentHeading?: string | null;
  paragraphHeading?: string | null;
};

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
};

type AttachedDoc = {
  documentId: string;
  filename: string;
};

type Props = {
  role: ChatRole;
  content: string;
  attachedDocs?: AttachedDoc[];
  references?: Reference[];
  onViewReference?: (documentId: string, pageNumber: number) => void;
  onOpenDocument?: (documentId: string) => void;
  uploadedDocs?: UploadedDocument[];
};

export const ChatMessage: React.FC<Props> = ({
  role,
  content,
  attachedDocs = [],
  references = [],
  onViewReference,
  onOpenDocument,
  uploadedDocs = [],
}) => {
  const isUser = role === "user";

  // Get filename from document ID
  const getFilename = (documentId: string) => {
    const doc = uploadedDocs.find(d => d.documentId === documentId);
    return doc?.filename || documentId;
  };

  // Group references by document
  const groupedReferences = React.useMemo(() => {
    const groups: Record<string, Reference[]> = {};
    references.forEach((ref) => {
      const key = ref.documentId;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(ref);
    });
    return groups;
  }, [references]);

  // Get unique pages for a document
  const getUniquePages = (refs: Reference[]) => {
    const pages = [...new Set(refs.map(r => r.pageNumber))].sort((a, b) => a - b);
    return pages;
  };

  return (
    <div className={`flex gap-4 msg-enter ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
      )}
      
      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[75%]`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm ${
            isUser ? "msg-user" : "msg-bot"
          }`}
        >
          {isUser && attachedDocs.length > 0 && (
            <div className="mb-3 space-y-2">
              {attachedDocs.map((doc) => (
                <button
                  key={doc.documentId}
                  type="button"
                  onClick={() => onOpenDocument?.(doc.documentId)}
                  className="w-full text-left flex items-center gap-3 p-3 rounded-xl bg-white/10 border border-white/15 hover:bg-white/15 transition-colors"
                  title={doc.filename}
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/15 flex items-center justify-center">
                    <svg className="w-5 h-5 text-red-300" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-white truncate">{doc.filename}</div>
                    <div className="text-xs text-white/70">PDF</div>
                  </div>
                </button>
              ))}
            </div>
          )}
          <p className="whitespace-pre-wrap leading-relaxed">{content}</p>

          {!isUser && references.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <div className="flex items-center gap-1.5 mb-2">
                <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-xs font-medium text-slate-300 uppercase tracking-wide">
                  Sources ({references.length})
                </span>
              </div>
              
              <div className="space-y-1.5">
                {Object.entries(groupedReferences).map(([documentId, refs], idx) => {
                  const pages = getUniquePages(refs);
                  const filename = getFilename(documentId);
                  
                  return (
                    <div 
                      key={`${documentId}-${idx}`}
                      className="bg-slate-900/50 rounded-md border border-slate-700/40 overflow-hidden hover:border-indigo-500/30 transition-colors"
                    >
                      <div className="p-2">
                        {/* Document Name and Pages in one row */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <div className="w-4 h-4 rounded bg-red-500/10 flex items-center justify-center">
                              <svg className="w-2.5 h-2.5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <p className="text-xs font-medium text-slate-200 truncate max-w-[120px]" title={filename}>
                              {filename}
                            </p>
                          </div>
                          <div className="flex items-center gap-1 flex-wrap">
                            <span className="text-xs text-slate-500">•</span>
                            {pages.map((page, pageIdx) => (
                              <button
                                key={`${documentId}-page-${page}-${pageIdx}`}
                                onClick={() => onViewReference?.(documentId, page)}
                                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 hover:border-indigo-500/40 transition-all group"
                                title={`Open reference page ${page}`}
                              >
                                <span className="text-xs font-medium text-indigo-300 group-hover:text-indigo-200">
                                  {page}
                                </span>
                                <svg className="w-2.5 h-2.5 text-indigo-400 group-hover:text-indigo-300 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
          <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
    </div>
  );
};
