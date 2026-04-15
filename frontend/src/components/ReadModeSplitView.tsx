import React from "react";
import { ReadModePdfViewer } from "./ReadModePdfViewer";
import { ReadModeChat } from "./ReadModeChat";
import { TextSelectionPopup } from "./TextSelectionPopup";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  selectedText?: string;
  pageNumber?: number;
};

type Props = {
  documentId: string;
  filename: string;
  pdfUrl: string;
  onClose: () => void;
  authToken: string;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
};

const API_BASE = import.meta.env.VITE_API_URL;

export const ReadModeSplitView: React.FC<Props> = ({ 
  documentId, 
  filename, 
  pdfUrl, 
  onClose, 
  authToken,
  sidebarOpen = true,
  onToggleSidebar
}) => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [currentSelection, setCurrentSelection] = React.useState<{
    text: string;
    pageNumber: number;
  } | null>(null);
  const [selectionPopup, setSelectionPopup] = React.useState<{
    text: string;
    pageNumber: number;
    position: { x: number; y: number };
  } | null>(null);

  const handleTextSelect = (selection: { text: string; pageNumber: number; position: { x: number; y: number } }) => {
    setSelectionPopup(selection);
  };

  const handleAddToChat = () => {
    if (selectionPopup) {
      setCurrentSelection({
        text: selectionPopup.text,
        pageNumber: selectionPopup.pageNumber,
      });
      setSelectionPopup(null);
      // Clear browser selection
      window.getSelection()?.removeAllRanges();
    }
  };

  const handleSend = async (question: string) => {
    if (!question.trim() || isSending) return;

    // Add user message to UI
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      selectedText: currentSelection?.text,
      pageNumber: currentSelection?.pageNumber || currentPage,
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsSending(true);
    try {
      const payload = {
        session_id: sessionId,
        document_id: documentId,
        question,
        selected_text: currentSelection?.text || null,
        page_number: currentSelection?.pageNumber || currentPage,
      };

      const res = await fetch(`${API_BASE}/read-mode/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Read Mode chat request failed");
      }

      const data = await res.json();
      setSessionId(data.session_id);

      // Add assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Clear selection after sending
      setCurrentSelection(null);
    } catch (error) {
      console.error("Read Mode chat error:", error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-[#0a0a0a]">
      <div className="w-full h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#111111] border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            {!sidebarOpen && onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"
                aria-label="Open sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            <h2 className="text-base font-semibold text-slate-100">Read Mode</h2>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-sm text-slate-300 truncate max-w-md" title={filename}>
              {filename}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Close Read Mode"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Split View */}
        <div className="flex-1 flex overflow-hidden bg-[#0d0d0d]">
          {/* PDF Viewer - Left */}
          <div className="flex-1 border-r border-white/[0.06]">
            <ReadModePdfViewer
              pdfUrl={pdfUrl}
              filename={filename}
              onTextSelect={handleTextSelect}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
            />
          </div>

          {/* Chat - Right */}
          <div className="w-96 flex-shrink-0 bg-[#111111]">
            <ReadModeChat
              messages={messages}
              onSend={handleSend}
              isSending={isSending}
              currentSelection={currentSelection}
              onClearSelection={() => setCurrentSelection(null)}
            />
          </div>
        </div>
      </div>

      {/* Text Selection Popup */}
      {selectionPopup && (
        <TextSelectionPopup
          position={selectionPopup.position}
          onAddToChat={handleAddToChat}
          onClose={() => setSelectionPopup(null)}
        />
      )}
    </div>
  );
};
