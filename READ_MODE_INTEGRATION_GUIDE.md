# Read Mode Integration Guide

## Completed Tasks

### Backend (✅ Complete)
1. ✅ Created Read Mode models in `models/schemas.py`
2. ✅ Updated database schema with read mode collections
3. ✅ Created `services/read_mode_service.py` with context building logic
4. ✅ Updated `services/llm_service.py` with Read Mode response generation
5. ✅ Created `api/v1/read_mode.py` with all endpoints
6. ✅ Registered Read Mode router in `main.py`

### Frontend (✅ Complete)
1. ✅ Added react-pdf dependency to `package.json`
2. ✅ Created `ReadModePdfViewer.tsx` - PDF viewer with text selection
3. ✅ Created `TextSelectionPopup.tsx` - "Add to Chat" popup
4. ✅ Created `ReadModeChat.tsx` - Chat interface for read mode
5. ✅ Created `ReadModeSplitView.tsx` - Split view container
6. ✅ Updated `Sidebar.tsx` with mode selection buttons

## Remaining Integration Steps

### Step 1: Update App.tsx State

Add these state variables to App.tsx:

```typescript
const [readModeDoc, setReadModeDoc] = React.useState<UploadedDocument | null>(null);
const [readModePdfUrl, setReadModePdfUrl] = React.useState<string>("");
```

### Step 2: Add Read Mode Handler

Add this function to App.tsx:

```typescript
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
```

### Step 3: Pass Handler to Sidebar

Update the Sidebar component call in App.tsx:

```typescript
<Sidebar
  isOpen={sidebarOpen}
  onToggle={() => setSidebarOpen(!sidebarOpen)}
  uploadedDocs={uploadedDocs}
  onNewChat={handleNewChat}
  onDeleteDoc={handleDeleteDoc}
  onViewDoc={handleViewDoc}
  onOpenReadMode={handleOpenReadMode}  // ADD THIS LINE
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
```

### Step 4: Add Read Mode Split View to Render

Add this after the existing PdfViewer component in App.tsx:

```typescript
{readModeDoc && readModePdfUrl && (
  <ReadModeSplitView
    documentId={readModeDoc.documentId}
    filename={readModeDoc.filename}
    pdfUrl={readModePdfUrl}
    onClose={handleCloseReadMode}
    authToken={authToken || ""}
  />
)}
```

### Step 5: Add Import Statement

Add this import at the top of App.tsx:

```typescript
import { ReadModeSplitView } from "./components/ReadModeSplitView";
```

## Installation Steps

### Backend
No additional installation needed - all dependencies already present.

### Frontend
Run this command in the `frontend` directory:

```bash
npm install
```

This will install the new `react-pdf` dependency.

## Testing the Feature

### 1. Start Backend
```bash
# From project root
python main.py
```

### 2. Start Frontend
```bash
# From frontend directory
npm run dev
```

### 3. Test Flow
1. Login to the application
2. Upload a PDF document
3. In the sidebar, find the uploaded document
4. Click "Read Mode" button (blue button with book icon)
5. Split view opens with PDF on left, chat on right
6. Highlight text in the PDF
7. Click "Add to Chat" popup
8. Selected text appears in chat with page number
9. Type a question about the selected text
10. Get answer based only on selected text + page context

## API Endpoints

### POST /api/v1/read-mode/chat
Handle read mode questions with selected text context.

**Request:**
```json
{
  "session_id": "optional-session-id",
  "document_id": "doc-id",
  "question": "What does this mean?",
  "selected_text": "highlighted text",
  "page_number": 3
}
```

**Response:**
```json
{
  "answer": "This means...",
  "session_id": "session-id"
}
```

### GET /api/v1/read-mode/page-text/{document_id}/{page_number}
Get text content of a specific page.

**Response:**
```json
{
  "page_number": 3,
  "text": "Full page text...",
  "total_pages": 10
}
```

### GET /api/v1/read-mode/sessions/{session_id}
Get read mode session history.

**Response:**
```json
{
  "session_id": "session-id",
  "document_id": "doc-id",
  "messages": [
    {
      "id": "msg-id",
      "role": "user",
      "content": "What does this mean?",
      "selected_text": "highlighted text",
      "page_number": 3,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

## Key Differences from RAG Mode

| Feature | RAG Mode (Open in Chat) | Read Mode |
|---------|------------------------|-----------|
| Upload | Full document to vector DB | No upload |
| Context | Retrieved chunks via vector search | Selected text + page |
| References | Shows page numbers + snippets | No references |
| Scope | Whole document | Current selection |
| History | Persistent | Tagged with selections |
| Use Case | "Summarize this PDF" | "What does this paragraph mean?" |

## Troubleshooting

### PDF Not Loading
- Check that GridFS file ID exists in database
- Verify PDF is not corrupted
- Check browser console for errors

### Text Selection Not Working
- Ensure PDF has text layer (not scanned image)
- Check that react-pdf is properly configured
- Verify PDF.js worker is loading

### Chat Not Responding
- Check backend logs for errors
- Verify API endpoint is accessible
- Check authentication token is valid

### Selection Popup Not Appearing
- Ensure text is actually selected
- Check z-index of popup component
- Verify popup position calculation

## Future Enhancements

1. **Persistent Highlights**: Save user highlights across sessions
2. **Multi-Selection**: Allow multiple text selections in one question
3. **Page Annotations**: Add notes and comments to pages
4. **Export Chat**: Export read mode conversations
5. **Keyboard Shortcuts**: Add shortcuts for common actions
6. **Mobile Support**: Optimize for mobile/tablet devices
7. **Collaborative Reading**: Share read mode sessions with others
8. **Smart Suggestions**: Suggest related sections based on selection
