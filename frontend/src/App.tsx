import React from "react";
import { PdfUpload } from "./components/PdfUpload";
import { ChatInput } from "./components/ChatInput";
import { ChatMessage } from "./components/ChatMessage";
import { Sidebar } from "./components/Sidebar";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
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
};

const API_BASE = "http://localhost:5000/api/v1";

const App: React.FC = () => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [uploadedDocs, setUploadedDocs] = React.useState<UploadedDocument[]>([]);
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleUploaded = (info: { documentId: string; filename: string }) => {
    const newDoc: UploadedDocument = {
      documentId: info.documentId,
      filename: info.filename,
      uploadedAt: new Date(),
    };
    setUploadedDocs((prev) => [...prev, newDoc]);
    setMessages((prev) => [
      ...prev,
      {
        id: `sys-${Date.now()}`,
        role: "assistant",
        content: `✓ Successfully uploaded: ${info.filename}`,
      },
    ]);
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  const handleDeleteDoc = (documentId: string) => {
    setUploadedDocs((prev) => prev.filter((doc) => doc.documentId !== documentId));
  };

  const handleSend = async (question: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsSending(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          question,
        }),
      });

      if (!res.ok) {
        throw new Error("Chat request failed");
      }

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
          content:
            "Something went wrong while processing your question. Please try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        uploadedDocs={uploadedDocs}
        onNewChat={handleNewChat}
        onDeleteDoc={handleDeleteDoc}
        onUploaded={handleUploaded}
      />

      <div className="flex-1 flex flex-col">
        <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between bg-slate-900/50 backdrop-blur">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                aria-label="Open sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <div>
              <h1 className="text-base font-semibold text-slate-50">
                PDF Chatbot
              </h1>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            {uploadedDocs.length} document{uploadedDocs.length !== 1 ? 's' : ''} loaded
          </div>
        </header>

        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4">
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
                      Welcome to PDF Chatbot
                    </h2>
                    <p className="text-slate-400 max-w-md">
                      Upload your PDF documents and start asking questions. I'll provide answers with precise references to pages and sections.
                    </p>
                  </div>
                  {uploadedDocs.length === 0 && (
                    <div className="mt-4">
                      <PdfUpload onUploaded={handleUploaded} variant="large" />
                    </div>
                  )}
                  {uploadedDocs.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mt-6">
                      <button
                        onClick={() => handleSend("Summarize the main topics in the documents")}
                        className="p-4 rounded-xl border border-slate-700 hover:border-slate-600 hover:bg-slate-800/50 transition-all text-left"
                      >
                        <div className="text-sm font-medium text-slate-200">Summarize documents</div>
                        <div className="text-xs text-slate-400 mt-1">Get an overview of the content</div>
                      </button>
                      <button
                        onClick={() => handleSend("What are the key points discussed?")}
                        className="p-4 rounded-xl border border-slate-700 hover:border-slate-600 hover:bg-slate-800/50 transition-all text-left"
                      >
                        <div className="text-sm font-medium text-slate-200">Key points</div>
                        <div className="text-xs text-slate-400 mt-1">Extract main ideas</div>
                      </button>
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
                      references={msg.references}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-slate-800 bg-slate-900/50 backdrop-blur">
            <div className="max-w-3xl mx-auto px-4 py-4">
              <ChatInput 
                onSend={handleSend} 
                disabled={uploadedDocs.length === 0 || isSending}
                isLoading={isSending}
              />
              {uploadedDocs.length === 0 && (
                <p className="mt-2 text-xs text-center text-amber-400/80">
                  Upload at least one PDF to start chatting
                </p>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;

