import React from "react";
import { PdfUpload } from "./components/PdfUpload";
import { ChatInput } from "./components/ChatInput";
import { ChatMessage } from "./components/ChatMessage";
import { Sidebar } from "./components/Sidebar";
import { PdfViewer } from "./components/PdfViewer";
import { AuthForm } from "./components/AuthForm";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  attachedDocs?: { documentId: string; filename: string }[];
  references?: {
    documentId: string;
    pageNumber: number;
    documentHeading?: string | null;
    paragraphHeading?: string | null;
  }[];
};

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
  initialPage?: number;
};

type AttachedDoc = {
  documentId: string;
  filename: string;
};

type ChatSession = {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
  sessionId: string | null;
};

const API_BASE = "http://localhost:5000/api/v1";

const App: React.FC = () => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [uploadedDocs, setUploadedDocs] = React.useState<UploadedDocument[]>([]);
  const [lastAttachedDocs, setLastAttachedDocs] = React.useState<AttachedDoc[] | null>(null);
  const [currentlyAttachedDocs, setCurrentlyAttachedDocs] = React.useState<UploadedDocument[]>([]);
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [viewingDoc, setViewingDoc] = React.useState<UploadedDocument | null>(null);
  const [uploadingFiles, setUploadingFiles] = React.useState<Map<string, number>>(new Map());
  const [chatSessions, setChatSessions] = React.useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = React.useState<string | null>(null);
  const [viewMode, setViewMode] = React.useState<"chat" | "uploads">("chat");
  const [attachmentResetKey, setAttachmentResetKey] = React.useState(0);
  const [authToken, setAuthToken] = React.useState<string | null>(() => localStorage.getItem("pdfchat_token"));
  const [currentUserEmail, setCurrentUserEmail] = React.useState<string | null>(() => localStorage.getItem("pdfchat_email"));
  const [theme, setTheme] = React.useState<"dark" | "light">(
    () => (localStorage.getItem("pdfchat_theme") as "dark" | "light") || "dark"
  );
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const uploadTriggerRef = React.useRef<(() => void) | null>(null);
  const isLoadingRef = React.useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    const t = setTimeout(() => scrollToBottom(), 50);
    return () => clearTimeout(t);
  }, [messages]);

  React.useEffect(() => {
    document.body.dataset.theme = theme;
    localStorage.setItem("pdfchat_theme", theme);
  }, [theme]);

  React.useEffect(() => {
    if (!authToken || isLoadingRef.current) return;
    
    isLoadingRef.current = true;
    const loadInitial = async () => {
      try {
        const [sessionsRes, docsRes] = await Promise.all([
          fetch(`${API_BASE}/chat/sessions`, {
            headers: { Authorization: `Bearer ${authToken}` },
          }),
          fetch(`${API_BASE}/documents`, {
            headers: { Authorization: `Bearer ${authToken}` },
          }),
        ]);
        if (sessionsRes.ok) {
          const sessionsData = await sessionsRes.json();
          setChatSessions(
            sessionsData.map((s: any) => ({
              id: s.id,
              title: s.title || "New chat",
              timestamp: new Date(s.updated_at || s.created_at),
              messages: [],
              sessionId: s.id,
            }))
          );
        }
        if (docsRes.ok) {
          const docsData = await docsRes.json();
          // Deduplicate documents by filename, keeping the most recent entry.
          const byFilename = new Map<string, { id: string; filename: string; created_at: string }>();
          for (const d of docsData) {
            const existing = byFilename.get(d.filename);
            if (!existing || new Date(d.created_at) > new Date(existing.created_at)) {
              byFilename.set(d.filename, { id: d.id, filename: d.filename, created_at: d.created_at });
            }
          }
          const uniqueDocs: UploadedDocument[] = Array.from(byFilename.values()).map((d) => ({
            documentId: d.id,
            filename: d.filename,
            uploadedAt: new Date(d.created_at),
          }));
          setUploadedDocs(uniqueDocs);
        }
      } catch (e) {
        console.error(e);
      } finally {
        isLoadingRef.current = false;
      }
    };
    loadInitial();
  }, [authToken]);

  const handleUploadStart = (filename: string) => {
    console.log(`🚀 Upload started: ${filename}`);
    setUploadingFiles((prev) => {
      const next = new Map(prev);
      // Avoid duplicate entries for the same filename while an upload is active
      if (!next.has(filename)) {
        next.set(filename, 0);
      }
      return next;
    });
  };


  const handleUploadProgress = (filename: string, progress: number) => {
    console.log(`📈 Upload progress for ${filename}: ${progress}%`);
    if (progress === -1) {
      setUploadingFiles((prev) => {
        const next = new Map(prev);
        next.delete(filename);
        return next;
      });
      return;
    }

    setUploadingFiles((prev) => {
      const next = new Map(prev);
      next.set(filename, progress);
      return next;
    });
  };

  const handleUploaded = (info: { documentId: string; filename: string }) => {
    console.log(`✅ Upload completed: ${info.filename}`, info);
    console.log(`📋 Document ID: ${info.documentId}`);

    setUploadedDocs((prev) => {
      const newDoc: UploadedDocument = {
        documentId: info.documentId,
        filename: info.filename,
        uploadedAt: new Date(),
      };

      console.log(`📝 Adding document to state:`, newDoc);
      console.log(`📚 Previous docs count: ${prev.length}`);

      // Deduplicate by filename: if a document with the same filename
      // already exists, replace it with the newest upload instead of
      // showing it multiple times.
      const withoutSameName = prev.filter((doc) => doc.filename !== info.filename);
      const newDocs = [...withoutSameName, newDoc];
      console.log(`📚 New docs count: ${newDocs.length}`);
      return newDocs;
    });
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setCurrentSessionId(null);
    // Clear any remembered document attachments so the new chat
    // does not implicitly reuse PDFs from previous conversations.
    setLastAttachedDocs(null);
    // Also reset ChatInput attachment state so the chips area is
    // empty for a brand new conversation (while keeping history
    // in the sidebar intact).
    setAttachmentResetKey((k) => k + 1);
  };

  const handleSelectSession = async (id: string) => {
    if (!authToken) return;
    try {
      const res = await fetch(`${API_BASE}/chat/sessions/${id}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (!res.ok) throw new Error("Failed to load chat session");
      const data = await res.json();
      setCurrentSessionId(id);
      setSessionId(data.session_id);
      const loadedMessages: Message[] = data.messages.map((m: any) => ({
        id: `${m.id}`,
        role: m.role,
        content: m.content,
      }));
      setMessages(loadedMessages);
      // When switching to another saved chat, clear the current
      // ChatInput attachments so each session starts clean.
      setAttachmentResetKey((k) => k + 1);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!authToken) return;
    try {
      await fetch(`${API_BASE}/chat/sessions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setChatSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        setMessages([]);
        setCurrentSessionId(null);
        setSessionId(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteDoc = async (documentId: string) => {
    if (!authToken) return;
    
    try {
      const res = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${authToken}` },
      });
      
      if (!res.ok) {
        throw new Error("Failed to delete document");
      }
      
      // Remove from frontend state
      setUploadedDocs((prev) => prev.filter((doc) => doc.documentId !== documentId));
      
      // Close viewer if this document is being viewed
      if (viewingDoc?.documentId === documentId) {
        setViewingDoc(null);
      }
      
      console.log(`🗑️ Document deleted: ${documentId}`);
    } catch (error) {
      console.error("Error deleting document:", error);
      alert("Failed to delete document. Please try again.");
    }
  };

  const handleViewDoc = (doc: UploadedDocument) => {
    setViewingDoc(doc);
  };

  const handleViewReference = (documentId: string, pageNumber: number) => {
    const doc = uploadedDocs.find(d => d.documentId === documentId);
    if (doc) {
      setViewingDoc({ ...doc, initialPage: pageNumber });
    }
  };


  const handleSend = async (question: string, attachedDocs?: AttachedDoc[]) => {
    const docsToAttach: AttachedDoc[] =
      attachedDocs ??
      lastAttachedDocs ??
      uploadedDocs.map((d) => ({ documentId: d.documentId, filename: d.filename }));

    // Remember the documents used for this conversation so that
    // follow‑up questions without explicit attachments keep using
    // the same PDF(s).
    if (docsToAttach.length > 0) {
      setLastAttachedDocs(docsToAttach);
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      attachedDocs: docsToAttach.length > 0 ? docsToAttach : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsSending(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({ session_id: sessionId, question }),
      });

      if (!res.ok) throw new Error("Chat request failed");

      const data = await res.json();
      setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.answer,
          references: data.references?.map((ref: any) => ({
            documentId: ref.document_id,
            pageNumber: ref.page_number,
            documentHeading: ref.document_heading,
            paragraphHeading: ref.paragraph_heading,
          })),
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: "Something went wrong while processing your question. Please try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };


  const uploadingFilesList = Array.from(uploadingFiles.entries()).map(([filename, progress]) => ({
    filename,
    progress,
  }));

  if (!authToken || !currentUserEmail) {
    return (
      <div className="flex h-screen items-center justify-center app-bg">
        <div className="w-full max-w-md rounded-2xl bg-[var(--bg-input)] p-6 border border-white/10 shadow-xl space-y-4">
          <h1 className="text-xl font-semibold text-slate-50 text-center">Sign in to PDF Chatbot</h1>
          <AuthForm
            onAuthenticated={(token: string, email: string) => {
              setAuthToken(token);
              setCurrentUserEmail(email);
              localStorage.setItem("pdfchat_token", token);
              localStorage.setItem("pdfchat_email", email);
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen app-bg">
      <PdfUpload
        variant="hidden"
        onUploaded={handleUploaded}
        onUploadStart={handleUploadStart}
        onUploadProgress={handleUploadProgress}
        uploadTriggerRef={uploadTriggerRef}
        authToken={authToken}
      />
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        uploadedDocs={uploadedDocs}
        onNewChat={handleNewChat}
        onDeleteDoc={handleDeleteDoc}
        onViewDoc={handleViewDoc}
        uploadTriggerRef={uploadTriggerRef}
        chatSessions={chatSessions}
        activeSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onDeleteSession={handleDeleteSession}
        currentUserEmail={currentUserEmail}
        onLogout={() => {
          localStorage.removeItem("pdfchat_token");
          localStorage.removeItem("pdfchat_email");
          setAuthToken(null);
          setCurrentUserEmail(null);
          setMessages([]);
          setUploadedDocs([]);
          setChatSessions([]);
        }}
      />

      {viewingDoc && (
        <PdfViewer
          documentId={viewingDoc.documentId}
          filename={viewingDoc.filename}
          initialPage={viewingDoc.initialPage}
          onClose={() => setViewingDoc(null)}
        />
      )}

      <div className="flex-1 flex flex-col chat-bg">
        <header className="header-bar px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"
                aria-label="Open sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <div>
              <h1 className="text-base font-semibold text-slate-50">PDF Chatbot</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-lg border border-white/10 text-xs text-slate-200 hover:bg-white/10"
            >
              {theme === "dark" ? "Light" : "Dark"} mode
            </button>
            <div className="doc-badge flex items-center gap-2">
            <svg className="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-semibold text-slate-200">{uploadedDocs.length}</span>
            <span className="text-xs text-slate-400">document{uploadedDocs.length !== 1 ? "s" : ""}</span>
          </div>
          </div>
        </header>


        <main className="flex-1 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 min-h-0">
            <div className="max-w-3xl mx-auto py-8">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-6 py-12">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-slate-100 mb-2">Welcome to PDF Chatbot</h2>
                    <p className="text-slate-400 max-w-md">
                      Upload your PDF documents and start asking questions. I'll provide answers with precise references to pages and sections.
                    </p>
                  </div>
                  
                  {uploadedDocs.length === 0 && uploadingFiles.size === 0 && (
                    <button
                      type="button"
                      onClick={() => uploadTriggerRef.current?.()}
                      className="mt-4 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 cursor-pointer transition-colors shadow-lg"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span>Upload PDF</span>
                    </button>
                  )}

                  {currentlyAttachedDocs.length > 0 && (
                    <div className="w-full max-w-2xl mt-8">
                      <h3 className="text-sm font-semibold text-slate-300 mb-4">Try asking:</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <button
                          onClick={() => {
                            const attachedDocs = currentlyAttachedDocs.map(d => ({ documentId: d.documentId, filename: d.filename }));
                            handleSend("Summarize this PDF and provide key points", attachedDocs);
                          }}
                          className="suggestion-card text-left"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                              <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-200">Summarize this PDF</p>
                              <p className="text-xs text-slate-400 mt-0.5">Get a quick overview and key points</p>
                            </div>
                          </div>
                        </button>

                        <button
                          onClick={() => {
                            const attachedDocs = currentlyAttachedDocs.map(d => ({ documentId: d.documentId, filename: d.filename }));
                            handleSend("What are the main topics covered in this document?", attachedDocs);
                          }}
                          className="suggestion-card text-left"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
                              <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                              </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-200">Main topics</p>
                              <p className="text-xs text-slate-400 mt-0.5">Discover what this document covers</p>
                            </div>
                          </div>
                        </button>

                        <button
                          onClick={() => {
                            const attachedDocs = currentlyAttachedDocs.map(d => ({ documentId: d.documentId, filename: d.filename }));
                            handleSend("Explain the key concepts in simple terms", attachedDocs);
                          }}
                          className="suggestion-card text-left"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                              </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-200">Explain key concepts</p>
                              <p className="text-xs text-slate-400 mt-0.5">Break down complex ideas</p>
                            </div>
                          </div>
                        </button>

                        <button
                          onClick={() => {
                            const attachedDocs = currentlyAttachedDocs.map(d => ({ documentId: d.documentId, filename: d.filename }));
                            handleSend("List the most important points from this document", attachedDocs);
                          }}
                          className="suggestion-card text-left"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                              <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                              </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-200">Important points</p>
                              <p className="text-xs text-slate-400 mt-0.5">Get a bulleted list of highlights</p>
                            </div>
                          </div>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {messages.map((msg) => (
                    <ChatMessage
                      key={msg.id}
                      role={msg.role}
                      content={msg.content}
                      attachedDocs={msg.attachedDocs}
                      references={msg.references}
                      onViewReference={handleViewReference}
                      onOpenDocument={(documentId) => {
                        const doc = uploadedDocs.find((d) => d.documentId === documentId);
                        if (doc) setViewingDoc(doc);
                      }}
                      uploadedDocs={uploadedDocs}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-white/5 bg-[var(--bg-input)]/50 backdrop-blur-sm py-4">
            <div className="px-4">
              <ChatInput
                onSend={handleSend}
                disabled={isSending}
                isLoading={isSending}
                onRequestUpload={() => uploadTriggerRef.current?.()}
                uploadedDocs={uploadedDocs}
                onViewDoc={handleViewDoc}
                hasDocuments={uploadedDocs.length > 0}
                uploadingFiles={uploadingFilesList}
                onAttachedDocsChange={setCurrentlyAttachedDocs}
                // Changing this key tells ChatInput to clear its
                // per-chat attachment state (used for "New Chat"
                // and when switching between sessions).
                resetAttachmentsKey={attachmentResetKey}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
   
export default App;

