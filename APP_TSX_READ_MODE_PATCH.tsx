// ADD THIS IMPORT AT THE TOP OF App.tsx (after other imports)
import { ReadModeSplitView } from "./components/ReadModeSplitView";

// ADD THESE STATE VARIABLES (after existing state declarations)
const [readModeDoc, setReadModeDoc] = React.useState<UploadedDocument | null>(null);
const [readModePdfUrl, setReadModePdfUrl] = React.useState<string>("");

// ADD THESE HANDLER FUNCTIONS (after existing handlers like handleViewDoc)
const handleOpenReadMode = async (doc: UploadedDocument) => {
  if (!authToken) return;
  
  try {
    // Fetch PDF URL
    const response = await fetch(`${API_BASE}/documents/${doc.documentId}/view`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    if (!response.ok) {
      throw new Error("Failed to load PDF");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    setReadModePdfUrl(url);
    setReadModeDoc(doc);
  } catch (error) {
    console.error("Error opening Read Mode:", error);
    alert("Failed to open document in Read Mode");
  }
};

const handleCloseReadMode = () => {
  if (readModePdfUrl) {
    URL.revokeObjectURL(readModePdfUrl);
  }
  setReadModePdfUrl("");
  setReadModeDoc(null);
};

// UPDATE THE SIDEBAR COMPONENT CALL - ADD onOpenReadMode prop
<Sidebar
  isOpen={sidebarOpen}
  onToggle={() => setSidebarOpen(!sidebarOpen)}
  uploadedDocs={uploadedDocs}
  onNewChat={handleNewChat}
  onDeleteDoc={handleDeleteDoc}
  onViewDoc={handleViewDoc}
  onOpenReadMode={handleOpenReadMode}  // <-- ADD THIS LINE
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

// ADD THIS COMPONENT AFTER THE EXISTING PdfViewer COMPONENT
{readModeDoc && readModePdfUrl && (
  <ReadModeSplitView
    documentId={readModeDoc.documentId}
    filename={readModeDoc.filename}
    pdfUrl={readModePdfUrl}
    onClose={handleCloseReadMode}
    authToken={authToken || ""}
  />
)}
