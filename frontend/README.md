# PDF ChatBot Frontend

A modern React + TypeScript frontend for the PDF ChatBot application that allows users to upload PDFs and chat with them using AI.

## 🚀 Live Demo

**Backend API:** https://pdf-chatbot-kktm.onrender.com

## 📋 Prerequisites

- Node.js (v16 or higher)
- npm or yarn package manager

## 🛠️ Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## ⚙️ Configuration

Create a `.env` file in the `frontend` directory with the following:

```env
VITE_API_URL=https://pdf-chatbot-kktm.onrender.com
```

For local development, you can use:
```env
VITE_API_URL=http://localhost:8000
```

## 🏃 Running the Application

### Development Mode

Start the development server with hot reload:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Production Build

Build the application for production:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## 📱 Features

### 1. User Authentication
- **Sign Up**: Create a new account with username and password
- **Login**: Access your account and chat history
- **Session Management**: Automatic token-based authentication

### 2. PDF Upload
- Upload PDF documents (max 10MB)
- Real-time upload progress tracking
- Automatic text extraction and embedding generation
- Support for multiple documents per user

### 3. Chat Interface
- Interactive chat with your uploaded PDFs
- Markdown rendering for formatted responses
- Message history persistence
- Real-time streaming responses
- Context-aware conversations

### 4. Document Management
- View all uploaded documents
- Select active document for chat
- Delete documents when no longer needed
- Document metadata display

## 🎯 How to Use

### Step 1: Create an Account

1. Open the application
2. Click on "Sign Up" tab
3. Enter a username and password (min 6 characters)
4. Click "Sign Up"

### Step 2: Upload a PDF

1. After logging in, you'll see the upload section
2. Click "Choose PDF" or drag and drop a PDF file
3. Wait for the upload and processing to complete
4. Your document will appear in the sidebar

### Step 3: Chat with Your PDF

1. Select a document from the sidebar (if you have multiple)
2. Type your question in the chat input
3. Press Enter or click Send
4. The AI will respond based on your PDF content

### Example Questions:
- "What is this document about?"
- "Summarize the key points"
- "Explain the section about [topic]"
- "What are the main conclusions?"

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── AuthForm.tsx          # Login/Signup component
│   │   ├── ChatInput.tsx         # Message input component
│   │   ├── ChatMessage.tsx       # Message display component
│   │   ├── PdfUpload.tsx         # PDF upload component
│   │   ├── PdfViewer.tsx         # Document viewer component
│   │   ├── Sidebar.tsx           # Document list sidebar
│   │   └── UploadProgress.tsx    # Upload progress indicator
│   ├── App.tsx                   # Main application component
│   ├── main.tsx                  # Application entry point
│   └── styles.css                # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.cjs
```

## 🎨 Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **React Markdown**: Markdown rendering
- **Lucide React**: Icon library

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## 🌐 API Endpoints Used

The frontend communicates with these backend endpoints:

- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/documents/upload` - Upload PDF
- `GET /api/v1/documents` - List user documents
- `DELETE /api/v1/documents/{doc_id}` - Delete document
- `POST /api/v1/chat` - Send chat message

## 🚨 Troubleshooting

### CORS Issues
If you encounter CORS errors, ensure the backend is configured to allow requests from your frontend origin.

### Upload Failures
- Check file size (max 10MB)
- Ensure file is a valid PDF
- Verify backend is running and accessible

### Authentication Issues
- Clear browser localStorage and try again
- Check if token has expired (re-login)
- Verify API URL in `.env` file

### Chat Not Working
- Ensure you have uploaded at least one PDF
- Check browser console for errors
- Verify backend API is responding

## 📦 Deployment

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
vercel
```

### Deploy to Netlify

1. Build the project:
```bash
npm run build
```

2. Deploy the `dist` folder to Netlify

### Environment Variables

Make sure to set `VITE_API_URL` in your deployment platform's environment variables.

## 🔐 Security Notes

- Passwords are hashed on the backend
- JWT tokens are used for authentication
- Tokens are stored in localStorage
- All API requests include authentication headers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the PDF ChatBot application.

## 🆘 Support

For issues or questions:
- Check the troubleshooting section
- Review backend logs at Render dashboard
- Open an issue on GitHub

## 🎉 Tips for Best Results

1. **Upload Quality PDFs**: Clear, text-based PDFs work best
2. **Ask Specific Questions**: More specific questions get better answers
3. **Use Context**: Reference previous messages in your questions
4. **Be Patient**: First message after upload may take a few seconds
5. **Re-upload if Needed**: If embeddings change, you may need to re-upload documents

---

**Happy Chatting! 🚀📄💬**
