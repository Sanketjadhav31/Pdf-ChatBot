import React from "react";
import { PdfUpload } from "./components/PdfUpload";
import { ChatInput } from "./components/ChatInput";
import { ChatMessage } from "./components/ChatMessage";
import { Sidebar } from "./components/Sidebar";
import { PdfViewer } from "./components/PdfViewer";
import { ReadModeSplitView } from "./components/ReadModeSplitView";
import { ReadModeSelector } from "./components/ReadModeSelector";
import { AuthForm } from "./components/AuthForm";
import { ToastContainer } from "./components/Toast";

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

type Toast = {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
};

const API_BASE = import.meta.env.VITE_API_URL;

const App: React.FC = () => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [uploadedDocs, setUploadedDocs] = React.useState<UploadedDocument[]>([]);
  const [chatDocs, setChatDocs] = React.useState<UploadedDocument[]>([]);
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
  const [currentUserEmail, setCurrentUserEmail] = React.useState<string | null>(null);
  const [currentUsername, setCurrentUsername] = React.useState<string | null>(null);
  const [theme, setTheme] = React.useState<"dark" | "light">(
    () => (localStorage.getItem("pdfchat_theme") as "dark" | "light") || "dark"
  );
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const uploadTriggerRef = React.useRef<(() => void) | null>(null);
  const isLoadingRef = React.useRef(false);
  const chatInputRef = React.useRef<HTMLTextAreaElement>(null);

  // Toast notifications state
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  // Read Mode state
  const [readModeDoc, setReadModeDoc] = React.useState<UploadedDocument | null>(null);
  const [readModePdfUrl, setReadModePdfUrl] = React.useState<string>("");
  const [showReadModeSelector, setShowReadModeSelector] = React.useState(false);
  const [autoOpenInReadMode, setAutoOpenInReadMode] = React.useState(false);
  const [isLoadingReadMode, setIsLoadingReadMode] = React.useState(false);

  // Toast helper functions
  const showToast = (message: string, type: "success" | "error" | "info" | "warning" = "success") => {
    const id = `toast-${Date.now()}`;
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  // Auto-focus chat input when user starts typing anywhere
  React.useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+U to trigger upload
      if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        uploadTriggerRef.current?.();
        return;
      }

      // Don't interfere if:
      // - User is holding modifier keys (Ctrl, Cmd, Alt)
      // - User is already typing in an input/textarea
      // - Chat is sending a message
      // - Not authenticated
      // - Viewing a PDF
      if (
        e.ctrlKey ||
        e.metaKey ||
        e.altKey ||
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        isSending ||
        !authToken ||
        viewingDoc
      ) {
        return;
      }

      // Focus the chat input if user types a printable character
      if (e.key.length === 1 && chatInputRef.current) {
        chatInputRef.current.focus();
        // Append to existing value instead of replacing
        const currentValue = chatInputRef.current.value;
        chatInputRef.current.value = currentValue + e.key;
        // Trigger React's onChange by dispatching input event
        const inputEvent = new Event('input', { bubbles: true });
        chatInputRef.current.dispatchEvent(inputEvent);
        // Prevent the default to avoid double typing
        e.preventDefault();
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown, true);
    return () => document.removeEventListener('keydown', handleGlobalKeyDown, true);
  }, [isSending, authToken, viewingDoc]);

  const refreshChatSessions = React.useCallback(async () => {
    if (!authToken) return;
    try {
      const sessionsRes = await fetch(`${API_BASE}/chat/sessions`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!sessionsRes.ok) return;
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
    } catch (e) {
      console.error("Failed to refresh chat sessions:", e);
    }
  }, [authToken]);

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
          const allDocs: UploadedDocument[] = docsData.map((d: any) => ({
            documentId: d.id,
            filename: d.filename,
            uploadedAt: new Date(d.created_at),
          }));
          setUploadedDocs(allDocs);
        }
      } catch (e) {
        console.error(e);
      } finally {
        isLoadingRef.current = false;
      }
    };
    loadInitial();
  }, [authToken]);

  React.useEffect(() => {
    if (!authToken) return;
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setCurrentUsername(data.username);
          setCurrentUserEmail(data.email);
        }
      })
      .catch(e => console.error("Failed to fetch user info:", e));
  }, [authToken]);

  // Debug logging for Read Mode state
  React.useEffect(() => {
    console.log(`🎨 Rendering - readModeDoc: ${readModeDoc ? 'SET (sidebar hidden)' : 'NULL (sidebar visible)'}`);
  }, [readModeDoc]);

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

    const newDoc: UploadedDocument = {
      documentId: info.documentId,
      filename: info.filename,
      uploadedAt: new Date(),
    };

    setUploadedDocs((prev) => {
      console.log(`📝 Adding document to state:`, newDoc);
      console.log(`📚 Previous docs count: ${prev.length}`);

      // Keep every upload as a separate document (dedupe only by id).
      const withoutSameId = prev.filter((doc) => doc.documentId !== info.documentId);
      const newDocs = [...withoutSameId, newDoc];
      console.log(`📚 New docs count: ${newDocs.length}`);
      return newDocs;
    });
    
    // Keep a chat-scoped doc list so each chat only shows its own PDFs.
    setChatDocs((prev) => {
      const withoutSameId = prev.filter((doc) => doc.documentId !== info.documentId);
      return [...withoutSameId, newDoc];
    });

    // If we're in Read Mode OR the upload was triggered from Read Mode context, automatically open in Read Mode
    if (readModeDoc || autoOpenInReadMode) {
      console.log(`🔄 Auto-opening newly uploaded PDF in Read Mode: ${info.filename}`);
      setAutoOpenInReadMode(false); // Reset the flag
      handleOpenReadMode(newDoc);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setCurrentSessionId(null);
    setChatDocs([]);
    setCurrentlyAttachedDocs([]);
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
    // Align session id immediately so /chat never uses a stale id or null while
    // history is still loading (avoids creating a new session or wrong-thread messages).
    setCurrentSessionId(id);
    setSessionId(id);
    try {
      const res = await fetch(`${API_BASE}/chat/sessions/${id}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (!res.ok) throw new Error("Failed to load chat session");
      const data = await res.json();
      setSessionId(data.session_id);
      const loadedMessages: Message[] = data.messages.map((m: any) => ({
        id: `${m.id}`,
        role: m.role,
        content: m.content,
        attachedDocs: (m.attached_docs ?? []).map((d: any) => ({
          documentId: d.document_id,
          filename: d.filename,
        })),
        references: (m.references ?? []).map((ref: any) => ({
          documentId: ref.document_id,
          pageNumber: ref.page_number,
          documentHeading: ref.document_heading,
          paragraphHeading: ref.paragraph_heading,
          snippet: ref.snippet,
          snippetHover: ref.snippet_hover,
        })),
      }));
      setMessages(loadedMessages);

      // Restore "active PDFs" for this chat session so the next /chat call
      // can build RAG context even after refresh.
      const sessionDocs: AttachedDoc[] = (data.documents ?? []).map((d: any) => ({
        documentId: d.document_id,
        filename: d.filename,
      }));
      setLastAttachedDocs(sessionDocs.length > 0 ? sessionDocs : null);
      setChatDocs(
        sessionDocs.map((d: AttachedDoc) => ({
          documentId: d.documentId,
          filename: d.filename,
          uploadedAt: new Date(),
        }))
      );
      setCurrentlyAttachedDocs(
        sessionDocs.map((d: AttachedDoc) => ({
          documentId: d.documentId,
          filename: d.filename,
          uploadedAt: new Date(),
        }))
      );
      // Keep ChatInput chips empty; we only need lastAttachedDocs for backend context.

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
      setChatDocs((prev) => prev.filter((doc) => doc.documentId !== documentId));
      setCurrentlyAttachedDocs((prev) => prev.filter((doc) => doc.documentId !== documentId));
      setLastAttachedDocs((prev) =>
        prev ? prev.filter((doc) => doc.documentId !== documentId) : null
      );
      
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

  const handleOpenInChat = async (doc: UploadedDocument) => {
    console.log(`📎 Opening document in chat: ${doc.filename} (${doc.documentId})`);
    
    // Close Read Mode if it's open
    if (readModeDoc) {
      console.log(`🔄 Closing Read Mode to switch to chat`);
      handleCloseReadMode();
    }
    
    // Check if document needs processing by calling backend
    try {
      const response = await fetch(`${API_BASE}/documents/${doc.documentId}/status`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      
      if (response.ok) {
        const status = await response.json();
        
        if (!status.has_chunks) {
          // Document needs processing - trigger the same workflow as upload
          console.log(`⚠️ Document ${doc.filename} needs processing`);
          
          // Show processing toast
          showToast(`Processing ${doc.filename}...`, "info");
          
          // Trigger processing
          const processResponse = await fetch(`${API_BASE}/documents/${doc.documentId}/process`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}` },
          });
          
          if (!processResponse.ok) {
            const errorData = await processResponse.json();
            const errorMessage = errorData.detail || 'Failed to process document';
            
            // Show error toast
            showToast(`Error: ${errorMessage}`, "error");
            
            console.error('Failed to process document:', errorMessage);
            return; // Don't add document to chat if processing failed
          }
          
          console.log(`✅ Document ${doc.filename} processed successfully`);
        }
      }
    } catch (error) {
      console.error('Error checking/processing document:', error);
      
      // Show error toast
      showToast(`Error processing ${doc.filename}. Please try again.`, "error");
      return; // Don't add document to chat if there was an error
    }
    
    // Add document to current chat session
    const docToAttach: AttachedDoc = {
      documentId: doc.documentId,
      filename: doc.filename,
    };
    
    // Update chat docs and currently attached docs
    setChatDocs((prev) => {
      const exists = prev.some((d) => d.documentId === doc.documentId);
      if (exists) {
        console.log(`📎 Document already in chat: ${doc.filename}`);
        return prev;
      }
      console.log(`📎 Adding document to chat: ${doc.filename}`);
      return [...prev, doc];
    });
    
    setCurrentlyAttachedDocs((prev) => {
      const exists = prev.some((d) => d.documentId === doc.documentId);
      if (exists) return prev;
      return [...prev, doc];
    });
    
    setLastAttachedDocs((prev) => {
      const exists = prev?.some((d) => d.documentId === doc.documentId);
      if (exists) return prev;
      return prev ? [...prev, docToAttach] : [docToAttach];
    });
    
    // Show success toast instead of chat message
    showToast(`📄 ${doc.filename} is ready! You can now ask questions about it.`, "success");
    
    // Switch to chat view
    setViewMode("chat");
    
    console.log(`✅ Document successfully opened in chat: ${doc.filename}`);
  };

  const handleOpenReadMode = async (doc: UploadedDocument) => {
    if (!authToken) return;
    
    setIsLoadingReadMode(true);
    
    try {
      console.log(`🔍 Opening Read Mode for document: ${doc.documentId}`);
      
      // Clean up previous PDF URL if switching documents
      if (readModePdfUrl && readModeDoc?.documentId !== doc.documentId) {
        URL.revokeObjectURL(readModePdfUrl);
        setReadModePdfUrl("");
      }
      
      // Fetch PDF as blob with proper headers
      const response = await fetch(`${API_BASE}/documents/${doc.documentId}/view`, {
        headers: { 
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        console.error(`❌ Failed to fetch PDF: ${response.status} ${response.statusText}`);
        throw new Error(`Failed to load PDF: ${response.statusText}`);
      }

      const blob = await response.blob();
      console.log(`✅ PDF blob received: ${blob.size} bytes, type: ${blob.type}`);
      
      // Verify it's a PDF
      if (!blob.type.includes('pdf') && blob.type !== 'application/octet-stream') {
        console.error(`❌ Invalid blob type: ${blob.type}`);
        throw new Error('Invalid PDF file type');
      }
      
      const url = URL.createObjectURL(blob);
      console.log(`✅ PDF URL created: ${url}`);
      
      setReadModePdfUrl(url);
      setReadModeDoc(doc);
      console.log(`✅ Read Mode state set for: ${doc.filename}`);
    } catch (error) {
      console.error("❌ Error opening Read Mode:", error);
      alert(`Failed to open document in Read Mode: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoadingReadMode(false);
    }
  };

  const handleCloseReadMode = () => {
    if (readModePdfUrl) {
      URL.revokeObjectURL(readModePdfUrl);
    }
    setReadModePdfUrl("");
    setReadModeDoc(null);
  };


  const handleSend = async (question: string, attachedDocs?: AttachedDoc[]) => {
    const explicitDocs: AttachedDoc[] = attachedDocs ?? [];
    // For backend context: if this message has explicit attachments, use those.
    // Otherwise fallback to last used docs for continuity.
    const effectiveDocsForRequest: AttachedDoc[] =
      explicitDocs.length > 0 ? explicitDocs : (lastAttachedDocs ?? []);

    // Remember the documents used for this conversation so that
    // follow‑up questions without explicit attachments keep using
    // the same PDF(s).
    if (effectiveDocsForRequest.length > 0) {
      setLastAttachedDocs(effectiveDocsForRequest);
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      // UI should show chips only when user explicitly attached/uploaded docs
      // on this specific message.
      attachedDocs: explicitDocs.length > 0 ? explicitDocs : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsSending(true);
    try {
      const payload: any = {
        session_id: sessionId ?? currentSessionId,
        question,
      };
      if (effectiveDocsForRequest.length > 0) {
        payload.document_ids = effectiveDocsForRequest.map((d) => d.documentId);
      }

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Chat request failed");

      const data = await res.json();
      setSessionId(data.session_id);
      setCurrentSessionId(data.session_id);

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
            snippet: ref.snippet,
            snippetHover: ref.snippet_hover,
          })),
        },
      ]);

      // Ensure the sidebar shows the newly created/updated session immediately.
      await refreshChatSessions();
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
            onAuthenticated={(token: string, email: string, username?: string) => {
              setAuthToken(token);
              setCurrentUserEmail(email);
              setCurrentUsername(username || null);
              localStorage.setItem("pdfchat_token", token);
            }}
          />
        </div>
      </div>
    );
  }

  // Loading overlay for Read Mode
  if (isLoadingReadMode) {
    return (
      <div className="flex h-screen items-center justify-center app-bg">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto">
            <svg className="animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-slate-100">Opening Read Mode</h2>
            <p className="text-slate-400">Loading your PDF document...</p>
          </div>
        </div>
      </div>
    );
  }

  // When in Read Mode, render Sidebar + Read Mode component
  if (readModeDoc && readModePdfUrl) {
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
          onOpenReadMode={handleOpenReadMode}
          onOpenInChat={handleOpenInChat}
          uploadTriggerRef={uploadTriggerRef}
          chatSessions={chatSessions}
          activeSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onDeleteSession={handleDeleteSession}
          currentUserEmail={currentUserEmail}
          currentUsername={currentUsername}
          onLogout={() => {
            localStorage.removeItem("pdfchat_token");
            setAuthToken(null);
            setCurrentUserEmail(null);
            setCurrentUsername(null);
            setMessages([]);
            setUploadedDocs([]);
            setChatDocs([]);
            setChatSessions([]);
          }}
        />
        <ReadModeSplitView
          documentId={readModeDoc.documentId}
          filename={readModeDoc.filename}
          pdfUrl={readModePdfUrl}
          onClose={handleCloseReadMode}
          authToken={authToken || ""}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
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
        onOpenReadMode={handleOpenReadMode}
        onOpenInChat={handleOpenInChat}
        uploadTriggerRef={uploadTriggerRef}
        chatSessions={chatSessions}
        activeSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onDeleteSession={handleDeleteSession}
        currentUserEmail={currentUserEmail}
        currentUsername={currentUsername}
        onLogout={() => {
          localStorage.removeItem("pdfchat_token");
          setAuthToken(null);
          setCurrentUserEmail(null);
          setCurrentUsername(null);
          setMessages([]);
          setUploadedDocs([]);
          setChatDocs([]);
          setChatSessions([]);
        }}
      />

          {viewingDoc && (
            <PdfViewer
              documentId={viewingDoc.documentId}
              filename={viewingDoc.filename}
              initialPage={viewingDoc.initialPage}
              onClose={() => setViewingDoc(null)}
              authToken={authToken || undefined}
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
                  onClick={() => setShowReadModeSelector(true)}
                  className="relative group px-4 py-2 rounded-lg border border-white/10 text-sm font-medium text-slate-200 hover:bg-white/5 hover:border-indigo-500/50 transition-all"
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                      />
                    </svg>
                    <span>Read Mode</span>
                  </div>
                  {/* Tooltip */}
                  <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg border border-slate-700 z-50">
                    Read PDFs with AI assistance - select text and ask questions
                    <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></span>
                  </span>
                </button>
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
                    <h2 className="text-2xl font-semibold text-slate-100 mb-2">
                      Hello {currentUsername ? currentUsername.trim().split(/\s+/)[0] : "there"}! 👋
                    </h2>
                    <p className="text-slate-400 max-w-md">
                      I'm your PDF Assistant. Upload a document and ask me anything about it. I can also respond to quick greetings and thanks.
                    </p>
                  </div>
                  
                  {uploadedDocs.length === 0 && uploadingFiles.size === 0 && (
                    <button
                      type="button"
                      onClick={() => uploadTriggerRef.current?.()}
                      className="mt-4 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 cursor-pointer transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 relative group"
                      title="Upload PDF files to start chatting"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span>Upload PDF</span>
                      {/* Tooltip */}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg border border-slate-700 z-50">
                        Click to upload PDF files (Ctrl+U)
                        <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></span>
                      </span>
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
                uploadedDocs={chatDocs}
                onViewDoc={handleViewDoc}
                hasDocuments={chatDocs.length > 0}
                uploadingFiles={uploadingFilesList}
                onAttachedDocsChange={setCurrentlyAttachedDocs}
                resetAttachmentsKey={attachmentResetKey}
                inputRef={chatInputRef}
              />
            </div>
          </div>
        </main>
      </div>

      {/* Read Mode Selector Modal */}
      <ReadModeSelector
        isOpen={showReadModeSelector}
        onClose={() => setShowReadModeSelector(false)}
        uploadedDocs={uploadedDocs}
        onSelectDocument={handleOpenReadMode}
        onUploadNew={() => {
          setAutoOpenInReadMode(true);
          uploadTriggerRef.current?.();
        }}
      />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
};
   
export default App;

