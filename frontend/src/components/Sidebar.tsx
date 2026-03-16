import React from "react";

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
  onViewDoc: (doc: UploadedDocument) => void;
  uploadTriggerRef?: React.MutableRefObject<(() => void) | null>;
  chatSessions?: { id: string; title: string; timestamp: Date }[];
  activeSessionId?: string | null;
  onSelectSession?: (id: string) => void;
  viewMode?: "chat" | "uploads";
  onViewModeChange?: (mode: "chat" | "uploads") => void;
  onDeleteSession?: (id: string) => void;
  currentUserEmail?: string | null;
  onLogout?: () => void;
};

export const Sidebar: React.FC<Props> = ({
  isOpen,
  onToggle,
  uploadedDocs,
  onNewChat,
  onDeleteDoc,
  onViewDoc,
  uploadTriggerRef,
  chatSessions = [],
  activeSessionId,
  onSelectSession,
  viewMode = "chat",
  onViewModeChange,
  onDeleteSession,
  currentUserEmail,
  onLogout,
}) => {
  const [searchQuery, setSearchQuery] = React.useState("");

  const truncateTitle = (title: string, maxLength: number = 28) => {
    if (!title) return "New chat";
    if (title.length <= maxLength) return title;
    return `${title.slice(0, maxLength - 3)}...`;
  };

  const filteredDocs = uploadedDocs.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="w-72 sidebar-bg flex flex-col">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h2 className="font-semibold text-slate-100">Documents</h2>
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"
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
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-slate-700 hover:bg-slate-800 transition-colors text-sm font-medium text-slate-200"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>

        {/* Upload button removed as requested; uploads can be triggered from main area */}
      </div>

      <div className="px-3 pb-3">
        <div className="flex items-center justify-between mb-2">
          <div className="inline-flex rounded-lg bg-slate-900 p-0.5">
            <button
              type="button"
              onClick={() => onViewModeChange?.("chat")}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                viewMode === "chat" 
                  ? "bg-slate-700 text-slate-100" 
                  : "text-slate-400"
              }`}
            >
              Chat history
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange?.("uploads")}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                viewMode === "uploads" 
                  ? "bg-slate-700 text-slate-100" 
                  : "text-slate-400"
              }`}
            >
              Uploaded PDFs
            </button>
          </div>
        </div>
        {viewMode === "uploads" && (
          <div className="relative mt-1">
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 pl-9 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-slate-600 transition-colors"
            />
            <svg
              className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="space-y-4">
          {viewMode === "chat" && chatSessions.length > 0 && (
            <div>
              <div className="flex items-center justify-between px-2 mb-2">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Recent Chats
                </h3>
              </div>
              <div className="space-y-1">
                {chatSessions.slice(0, 8).map((session) => (
                  <div key={session.id} className="flex items-center gap-1">
                    <button
                      onClick={() => onSelectSession?.(session.id)}
                      className={`flex-1 text-left px-3 py-2 rounded-lg text-sm transition-colors flex flex-col gap-0.5 ${
                        activeSessionId === session.id
                          ? "bg-slate-800 border border-slate-600 text-slate-100"
                          : "hover:bg-slate-800/70 border border-transparent hover:border-slate-700 text-slate-300"
                      }`}
                      title={session.title}
                    >
                      <span className="truncate">
                        {truncateTitle(session.title || "New chat")}
                      </span>
                      <span className="text-xs text-slate-500">
                        {session.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </button>
                    {onDeleteSession && (
                      <button
                        onClick={() => onDeleteSession(session.id)}
                        className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-red-400"
                        aria-label="Delete chat"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {viewMode === "uploads" && (
          <div>
          <div className="flex items-center justify-between px-2">
            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-400 [data-theme='light']_&:text-slate-600 uppercase tracking-wider">
              Uploaded PDFs
            </h3>
            <span className="text-xs font-bold text-indigo-400 dark:text-indigo-400 [data-theme='light']_&:text-indigo-600 bg-indigo-500/10 dark:bg-indigo-500/10 [data-theme='light']_&:bg-indigo-100 px-2 py-0.5 rounded-full">
              {filteredDocs.length}
            </span>
          </div>
          
          {uploadedDocs.length === 0 ? (
            <div className="text-center py-8 px-4">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800 dark:bg-slate-800 [data-theme='light']_&:bg-slate-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-slate-500 dark:text-slate-500 [data-theme='light']_&:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-500 [data-theme='light']_&:text-slate-600">No documents uploaded yet</p>
              <p className="text-xs text-slate-600 dark:text-slate-600 [data-theme='light']_&:text-slate-500 mt-1">Upload PDFs to get started</p>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="text-xs text-slate-500 dark:text-slate-500 [data-theme='light']_&:text-slate-600 px-2 py-4 text-center">
              No documents match your search
            </div>
          ) : (
            <div className="space-y-1">
              {filteredDocs.map((doc) => (
                <div
                  key={doc.documentId}
                  className="group flex items-start gap-2 p-3 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-800 [data-theme='light']_&:hover:bg-slate-50 border border-transparent hover:border-slate-700 dark:hover:border-slate-700 [data-theme='light']_&:hover:border-slate-200 transition-all cursor-pointer"
                  onClick={() => onViewDoc(doc)}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <svg className="w-5 h-5 text-red-400 dark:text-red-400 [data-theme='light']_&:text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 dark:text-slate-200 [data-theme='light']_&:text-slate-900 truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-500 [data-theme='light']_&:text-slate-500 mt-0.5">
                      {doc.uploadedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewDoc(doc);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-slate-700 dark:hover:bg-slate-700 [data-theme='light']_&:hover:bg-slate-200 rounded transition-all"
                      aria-label="View document"
                    >
                      <svg className="w-4 h-4 text-slate-400 dark:text-slate-400 [data-theme='light']_&:text-slate-600 hover:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteDoc(doc.documentId);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-slate-700 dark:hover:bg-slate-700 [data-theme='light']_&:hover:bg-slate-200 rounded transition-all"
                      aria-label="Delete document"
                    >
                      <svg className="w-4 h-4 text-slate-400 dark:text-slate-400 [data-theme='light']_&:text-slate-600 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          </div>
          )}
        </div>
      </div>

      <div className="p-3 border-t border-slate-800">
        <div className="text-xs text-slate-500 space-y-2">
          {currentUserEmail && (
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="truncate">{currentUserEmail}</span>
              </div>
              {onLogout && (
                <button
                  onClick={onLogout}
                  className="flex-shrink-0 p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-400"
                  aria-label="Logout"
                  title="Logout"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              )}
            </div>
          )}
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
