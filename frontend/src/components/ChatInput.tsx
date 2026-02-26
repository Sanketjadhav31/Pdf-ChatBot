import React from "react";
import { PdfUpload } from "./PdfUpload";
import { UploadProgress } from "./UploadProgress";

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
  onSend: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  onUploaded?: (info: { documentId: string; filename: string }) => void;
  onUploadStart?: (filename: string) => void;
  onUploadProgress?: (filename: string, progress: number) => void;
  uploadedDocs?: UploadedDocument[];
  onViewDoc?: (doc: UploadedDocument) => void;
  onDeleteDoc?: (documentId: string) => void;
};

export const ChatInput: React.FC<Props> = ({ 
  onSend, 
  disabled, 
  isLoading, 
  onUploaded,
  onUploadStart,
  onUploadProgress,
  uploadedDocs = [],
  onViewDoc,
  onDeleteDoc
}) => {
  const [value, setValue] = React.useState("");
  const [uploadingFiles, setUploadingFiles] = React.useState<UploadingFile[]>([]);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const handleUploadStartLocal = (filename: string) => {
    setUploadingFiles(prev => [...prev, { filename, progress: 0 }]);
    onUploadStart?.(filename);
  };

  const handleUploadProgressLocal = (filename: string, progress: number) => {
    if (progress === -1) {
      // Error occurred, remove from list
      setUploadingFiles(prev => prev.filter(file => file.filename !== filename));
    } else {
      setUploadingFiles(prev => {
        const existing = prev.find(f => f.filename === filename);
        if (existing) {
          return prev.map(file =>
            file.filename === filename ? { ...file, progress } : file
          );
        }
        return prev;
      });
    }
    onUploadProgress?.(filename, progress);
  };

  const handleUploadedLocal = (info: { documentId: string; filename: string }) => {
    setUploadingFiles(prev => prev.filter(file => file.filename !== info.filename));
    onUploaded?.(info);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
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

  const truncateFilename = (filename: string, maxLength: number = 15) => {
    if (filename.length <= maxLength) return filename;
    const extension = filename.split('.').pop();
    const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = nameWithoutExt.substring(0, maxLength - 3 - (extension?.length || 0));
    return `${truncatedName}...${extension}`;
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-3">
      <UploadProgress uploadingFiles={uploadingFiles} />

      {uploadedDocs.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 px-1">
            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Uploaded Documents ({uploadedDocs.length})
            </span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
            {uploadedDocs.map((doc) => (
              <div
                key={doc.documentId}
                className="flex-shrink-0 group relative"
              >
                <div className="flex items-center gap-2 p-2 pr-8 rounded-lg bg-slate-800/70 border border-slate-700 hover:border-slate-600 transition-all min-w-[140px] max-w-[180px]">
                  <div className="flex-shrink-0 w-8 h-8 rounded-md bg-red-500/10 flex items-center justify-center">
                    <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate" title={doc.filename}>
                      {truncateFilename(doc.filename)}
                    </p>
                    <p className="text-xs text-slate-500">
                      PDF
                    </p>
                  </div>
                </div>
                <div className="absolute top-1 right-1 flex items-center gap-0.5">
                  {onViewDoc && (
                    <button
                      onClick={() => onViewDoc(doc)}
                      className="p-1 rounded-md bg-slate-800/90 hover:bg-slate-700 border border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="View document"
                      title="Open PDF"
                    >
                      <svg className="w-3 h-3 text-slate-400 hover:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </button>
                  )}
                  {onDeleteDoc && (
                    <button
                      onClick={() => onDeleteDoc(doc.documentId)}
                      className="p-1 rounded-full bg-slate-900/90 hover:bg-red-500/20 border border-slate-700 hover:border-red-500 opacity-0 group-hover:opacity-100 transition-all"
                      aria-label="Delete document"
                      title="Remove PDF"
                    >
                      <svg className="w-3 h-3 text-slate-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="relative flex items-end gap-2"
      >
        <div className="flex-1 flex items-end gap-2 border border-slate-700 rounded-2xl px-4 py-3 bg-slate-800/50 shadow-lg focus-within:border-slate-600 transition-colors">
          {onUploaded && (
            <div className="flex-shrink-0 self-end pb-0.5">
              <PdfUpload 
                onUploaded={handleUploadedLocal}
                onUploadStart={handleUploadStartLocal}
                onUploadProgress={handleUploadProgressLocal}
                variant="input" 
              />
            </div>
          )}
          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-slate-500 resize-none max-h-[200px] min-h-[24px]"
            placeholder="Message PDF Chatbot..."
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
          />
        </div>
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 p-3 rounded-xl bg-indigo-500 text-white hover:bg-indigo-600 disabled:bg-slate-700 disabled:text-slate-500 transition-colors shadow-lg disabled:shadow-none"
          aria-label="Send message"
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
        </button>
      </form>
    </div>
  );
};

