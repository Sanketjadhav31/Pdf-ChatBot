# Read Mode Implementation Plan

## Overview
Implementing a new "Read Mode" feature that allows users to select text from PDFs and ask questions about specific selections, separate from the existing RAG-based "Open in Chat" mode.

## Architecture Summary

### Two Distinct Modes

**OPEN IN CHAT (Existing - RAG Pipeline)**
- Full document uploaded and chunked
- Embedded into vector DB
- RAG retrieval on every question
- User asks about whole document
- Conversation memory across turns

**READ MODE (New - Direct Context)**
- No full upload to vector DB
- Only selected text sent as context
- Selected text IS the context
- User asks about what they see
- Context resets on new selection

## Implementation Tasks

### Backend Tasks

#### 1. Create Read Mode Service (`services/read_mode_service.py`)
- [ ] Text selection context handler
- [ ] Page context extractor (from GridFS PDF)
- [ ] Conversation history manager with selection tagging
- [ ] Read Mode prompt builder

#### 2. Create Read Mode API Endpoint (`api/v1/read_mode.py`)
- [ ] POST `/api/v1/read-mode/chat` - Handle read mode questions
- [ ] GET `/api/v1/read-mode/page-text/{document_id}/{page_number}` - Get page text
- [ ] POST `/api/v1/read-mode/session` - Create/manage read mode sessions

#### 3. Update Database Schema (`database.py`)
- [ ] Add `read_mode_sessions` collection
- [ ] Add `read_mode_messages` collection with selection metadata
- [ ] Create indexes for read mode collections

#### 4. Update Models (`models/schemas.py`)
- [ ] `ReadModeRequest` - selection + question
- [ ] `ReadModeResponse` - answer without RAG references
- [ ] `TextSelection` - selected text metadata
- [ ] `ReadModeMessage` - message with selection context

### Frontend Tasks

#### 5. Create Read Mode PDF Viewer (`frontend/src/components/ReadModePdfViewer.tsx`)
- [ ] PDF rendering with react-pdf or pdf.js
- [ ] Text selection handler
- [ ] "Add to Chat" popup on selection
- [ ] Highlight overlay for referenced text
- [ ] Page navigation and zoom controls

#### 6. Create Read Mode Chat Panel (`frontend/src/components/ReadModeChat.tsx`)
- [ ] Chat interface for read mode
- [ ] Display selected text quotes
- [ ] Show page numbers with selections
- [ ] No reference/source display (different from RAG mode)

#### 7. Create Split View Container (`frontend/src/components/ReadModeSplitView.tsx`)
- [ ] Left panel: PDF viewer
- [ ] Right panel: Chat
- [ ] Shared state management
- [ ] Responsive layout

#### 8. Update Document List UI (`frontend/src/components/Sidebar.tsx`)
- [ ] Add mode selection buttons per document
- [ ] "📖 Read Mode" button
- [ ] "💬 Open in Chat" button
- [ ] Visual distinction between modes

#### 9. Update App State (`frontend/src/App.tsx`)
- [ ] Add read mode state management
- [ ] Route between chat mode and read mode
- [ ] Handle mode transitions

### Integration Tasks

#### 10. PDF Text Extraction Enhancement (`services/pdf_loader.py`)
- [ ] Add function to extract text by page number
- [ ] Add function to extract text by character range
- [ ] Cache page text for quick access

#### 11. LLM Service Update (`services/llm_service.py`)
- [ ] Add `generate_read_mode_response()` method
- [ ] Implement Read Mode prompt template
- [ ] Handle 3-layer context (selection + page + history)

#### 12. Main App Integration (`main.py`)
- [ ] Register read mode router
- [ ] Update CORS for new endpoints

## Data Flow

### Read Mode Session Flow
```
1. User clicks "Read Mode" on document
   ↓
2. Frontend opens split view (PDF left, Chat right)
   ↓
3. User highlights text in PDF
   ↓
4. "Add to Chat" button appears
   ↓
5. User clicks "Add to Chat"
   ↓
6. Selected text sent to chat panel as quote
   ↓
7. User types question
   ↓
8. POST /api/v1/read-mode/chat with:
   - selected_text
   - page_number
   - document_id
   - question
   - session_id
   ↓
9. Backend:
   - Fetches page context from GridFS
   - Loads last 3-5 conversation turns
   - Builds 3-layer prompt
   - Calls LLM
   ↓
10. Response sent back to chat panel
```

### State Management
```typescript
type ReadModeState = {
  document_id: string;
  current_page: number;
  selected_text: string | null;
  selection_position: {
    page: number;
    char_start: number;
    char_end: number;
  } | null;
  mode: "read_mode";
  session_id: string;
}
```

## Database Schema

### read_mode_sessions
```python
{
  "_id": str,  # session_id
  "user_id": str,
  "document_id": str,
  "created_at": datetime,
  "updated_at": datetime,
}
```

### read_mode_messages
```python
{
  "_id": str,
  "session_id": str,
  "user_id": str,
  "role": str,  # "user" or "assistant"
  "content": str,
  "selected_text": str | None,  # The text user selected
  "page_number": int | None,
  "char_start": int | None,
  "char_end": int | None,
  "created_at": datetime,
}
```

## API Endpoints

### POST /api/v1/read-mode/chat
```python
Request:
{
  "session_id": str | None,
  "document_id": str,
  "question": str,
  "selected_text": str | None,
  "page_number": int,
  "char_start": int | None,
  "char_end": int | None,
}

Response:
{
  "answer": str,
  "session_id": str,
}
```

### GET /api/v1/read-mode/page-text/{document_id}/{page_number}
```python
Response:
{
  "page_number": int,
  "text": str,
  "total_pages": int,
}
```

## Frontend Components Structure

```
frontend/src/components/
├── ReadModePdfViewer.tsx       # PDF display + text selection
├── ReadModeChat.tsx            # Chat panel for read mode
├── ReadModeSplitView.tsx       # Container for split view
├── TextSelectionPopup.tsx      # "Add to Chat" popup
└── SelectedTextQuote.tsx       # Display selected text in chat
```

## Implementation Priority

### Phase 1: Backend Foundation (Tasks 1-4)
1. Create read mode service
2. Create API endpoints
3. Update database schema
4. Update models

### Phase 2: Frontend Core (Tasks 5-7)
1. Create PDF viewer with selection
2. Create read mode chat panel
3. Create split view container

### Phase 3: Integration (Tasks 8-12)
1. Update sidebar with mode buttons
2. Update app state management
3. Enhance PDF text extraction
4. Update LLM service
5. Register routes in main app

### Phase 4: Testing & Polish
1. Test text selection accuracy
2. Test context building
3. Test conversation continuity
4. UI/UX refinements
5. Error handling

## Key Differences from RAG Mode

| Aspect | RAG Mode | Read Mode |
|--------|----------|-----------|
| Upload | Full document to vector DB | No upload needed |
| Context | Retrieved chunks | Selected text + page |
| References | Page numbers + snippets | No references shown |
| Scope | Whole document | Current selection |
| History | Persistent across selections | Tagged with selections |
| Prompt | RAG-specific | Read-assistant specific |

## Success Criteria

- [ ] User can select text in PDF viewer
- [ ] Selected text appears in chat as quote
- [ ] LLM answers strictly from selected text + page context
- [ ] Conversation history maintains selection context
- [ ] No RAG/vector search involved
- [ ] Mode selection works from document list
- [ ] Split view is responsive and functional
- [ ] Page navigation works smoothly
- [ ] Text selection is accurate
- [ ] Performance is acceptable (< 2s response time)
