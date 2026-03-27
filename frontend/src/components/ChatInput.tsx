import React from "react";

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
};

type UploadingFile = {
  filename: string;
  progress: number;
};

type Props = {
  onSend: (message: string, attachedDocs?: { documentId: string; filename: string }[]) => void;
  disabled?: boolean;
  isLoading?: boolean;
  onRequestUpload?: () => void;
  uploadedDocs?: UploadedDocument[];
  onViewDoc?: (doc: UploadedDocument) => void;
  hasDocuments?: boolean;
  uploadingFiles?: UploadingFile[];
  onAttachedDocsChange?: (docs: UploadedDocument[]) => void;
  resetAttachmentsKey?: number;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
};

export const ChatInput: React.FC<Props> = ({
  onSend,
  disabled,
  isLoading,
  onRequestUpload,
  uploadedDocs = [],
  onViewDoc,
  hasDocuments = false,
  uploadingFiles = [],
  onAttachedDocsChange,
  resetAttachmentsKey,
  inputRef: externalRef,
}) => {
  const [value, setValue] = React.useState("");
  const [attachedDocIds, setAttachedDocIds] = React.useState<string[]>([]);
  const [hasUserRemovedDocs, setHasUserRemovedDocs] = React.useState(false);
  const internalRef = React.useRef<HTMLTextAreaElement>(null);
  const textareaRef = externalRef || internalRef;
  const prevUploadedDocsRef = React.useRef<Set<string>>(new Set());

  // Clear attachments when resetAttachmentsKey changes (new chat/session)
  React.useEffect(() => {
    if (resetAttachmentsKey === undefined) return;
    console.log("♻️ Resetting ChatInput attachments due to new chat/session", {
      resetKey: resetAttachmentsKey,
    });
    setAttachedDocIds([]);
    setHasUserRemovedDocs(false);
    prevUploadedDocsRef.current = new Set(
      (uploadedDocs ?? []).map((d) => d.documentId)
    );
  }, [resetAttachmentsKey]);

  // Auto-attach newly uploaded documents
  React.useEffect(() => {
    console.log("📋 ChatInput docs effect", {
      uploadedDocsCount: uploadedDocs.length,
      prevTrackedCount: prevUploadedDocsRef.current.size,
      hasUserRemovedDocs,
      currentAttachedCount: attachedDocIds.length,
    });

    if (uploadedDocs.length === 0) {
      console.log("🧹 No documents, clearing ChatInput attachment state");
      setAttachedDocIds([]);
      setHasUserRemovedDocs(false);
      prevUploadedDocsRef.current = new Set();
      return;
    }

    const currentDocIds = new Set(uploadedDocs.map((d) => d.documentId));

    // Find truly new documents (not present in previous set)
    const newDocIds = uploadedDocs
      .filter((d) => !prevUploadedDocsRef.current.has(d.documentId))
      .map((d) => d.documentId);

    console.log("🔍 ChatInput new documents check", {
      newDocIds,
      newCount: newDocIds.length,
      hasUserRemovedDocs,
    });

    if (newDocIds.length > 0 && !hasUserRemovedDocs) {
      console.log("✅ Auto-attaching newly uploaded documents:", newDocIds);
      setAttachedDocIds((prev) => {
        const updated = [...prev, ...newDocIds];
        console.log("📌 ChatInput attachedDocIds updated:", updated);
        return updated;
      });
    } else if (newDocIds.length === 0) {
      // Remove attachments for documents that no longer exist
      setAttachedDocIds((prev) => {
        const availableIds = new Set(uploadedDocs.map((d) => d.documentId));
        const filtered = prev.filter((id) => availableIds.has(id));
        if (filtered.length !== prev.length) {
          console.log(
            "🗑️ Removed non-existent documents from ChatInput attachments"
          );
        }
        return filtered;
      });
    }

    prevUploadedDocsRef.current = currentDocIds;
  }, [uploadedDocs, hasUserRemovedDocs, attachedDocIds.length]);

  // Notify parent about currently attached documents
  React.useEffect(() => {
    if (onAttachedDocsChange) {
      const attached = uploadedDocs.filter((d) => attachedDocIds.includes(d.documentId));
      onAttachedDocsChange(attached);
    }
  }, [attachedDocIds, uploadedDocs, onAttachedDocsChange]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    const docsToAttach = uploadedDocs.filter((d) =>
      attachedDocIds.includes(d.documentId)
    );
    if (docsToAttach.length > 0) {
      onSend(
        trimmed,
        docsToAttach.map((d) => ({
          documentId: d.documentId,
          filename: d.filename,
        }))
      );
    } else {
      // No explicit attachments – delegate to parent to decide which
      // documents to use (e.g. last used document).
      onSend(trimmed);
    }
    setValue("");
    // After sending, clear attachment chips from the input, but keep
    // documents available in history / sidebar.
    setAttachedDocIds([]);
    setHasUserRemovedDocs(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  const truncateFilename = (filename: string, maxLength: number = 12) => {
    if (filename.length <= maxLength) return filename;
    const ext = filename.split(".").pop() || "";
    const name = filename.slice(0, filename.lastIndexOf("."));
    return `${name.slice(0, maxLength - ext.length - 4)}...${ext}`;
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className={`input-container flex flex-col rounded-2xl overflow-hidden ${!hasDocuments && uploadingFiles.length === 0 ? "input-pulse" : ""}`}>
          {/* Slim progress strip inside input - at top */}
          {uploadingFiles.length > 0 && (
            <div className="px-4 py-2 border-b border-white/5 bg-white/[0.02] space-y-1.5">
              {uploadingFiles.map((file) => (
                <div key={file.filename} className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-400 truncate">{truncateFilename(file.filename, 24)}</p>
                    <div className="mt-1 h-0.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 flex-shrink-0">{file.progress}%</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-start gap-2 px-4 py-3">
            {/* Paperclip - triggers sidebar upload */}
            <button
              type="button"
              onClick={onRequestUpload}
              className="flex-shrink-0 p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-all hover:scale-110 active:scale-95 relative group"
              aria-label="Upload PDF files"
              title="Upload PDF files (Ctrl+U)"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              {/* Enhanced Tooltip */}
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg border border-slate-700 z-50">
                Upload PDF files
                <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></span>
              </span>
            </button>

            {/* Document cards above textarea + full-width input below */}
            <div className="flex-1 flex flex-col gap-2 min-w-0">
              {uploadedDocs.length > 0 && attachedDocIds.length > 0 && (
                <div className="flex gap-2 overflow-x-auto pb-1 pr-1">
                  {uploadedDocs
                    .filter((doc) => attachedDocIds.includes(doc.documentId))
                    .map((doc) => (
                    <div
                      key={doc.documentId}
                      className="pdf-chip flex items-center gap-1.5 flex-shrink-0 max-w-full"
                    >
                      <svg className="w-3.5 h-3.5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                      <span className="truncate text-xs text-slate-200" title={doc.filename}>
                        {truncateFilename(doc.filename, 24)}
                      </span>
                      {onViewDoc && (
                        <button
                          type="button"
                          onClick={() => onViewDoc(doc)}
                          className="p-0.5 rounded hover:bg-white/10 text-slate-400 hover:text-indigo-400"
                          aria-label="View"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                          </svg>
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setAttachedDocIds((prev) =>
                            prev.filter((id) => id !== doc.documentId)
                          );
                          setHasUserRemovedDocs(true);
                        }}
                        className="p-0.5 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400"
                        aria-label="Remove from message"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <textarea
                ref={textareaRef}
                className="w-full bg-transparent outline-none text-sm text-slate-100 placeholder:text-slate-500 resize-none max-h-[200px] min-h-[32px]"
                placeholder={
                  hasDocuments
                    ? "Message PDF Chatbot..."
                    : "Ask me anything. Upload a PDF if you want document-grounded answers."
                }
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                disabled={false}
                rows={1}
              />
            </div>

            <button
              type="submit"
              disabled={disabled || !value.trim() || isLoading}
              className="send-btn flex-shrink-0 p-3 rounded-xl disabled:cursor-not-allowed transition-all hover:scale-110 active:scale-95 relative group"
              aria-label="Send message"
              title={disabled || !value.trim() || isLoading ? "Type a message to send" : "Send message (Enter)"}
            >
              {isLoading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
              {/* Tooltip for send button */}
              {!disabled && value.trim() && !isLoading && (
                <span className="absolute bottom-full right-0 mb-2 px-3 py-1.5 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg border border-slate-700 z-50">
                  Send message (Enter)
                  <span className="absolute top-full right-4 -mt-1 border-4 border-transparent border-t-slate-900"></span>
                </span>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
