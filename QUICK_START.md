# ⚡ Quick Start Guide - PDF ChatBot

## 🎯 For Netlify Deployment

### Copy-Paste Configuration

```
Base directory:      frontend
Build command:       npm run build
Publish directory:   frontend/dist
Branch:              main
```

### Environment Variable

```
VITE_API_URL=https://pdf-chatbot-kktm.onrender.com
```

**That's it!** Click Deploy and you're done! 🚀

---

## 📱 How to Use the App

### 1️⃣ Sign Up
- Open your deployed site
- Click "Sign Up" tab
- Enter username and password (min 6 chars)
- Click "Sign Up" button

### 2️⃣ Upload PDF
- Click "Choose PDF" button
- Select a PDF file (max 10MB)
- Wait for upload to complete
- Document appears in sidebar

### 3️⃣ Chat with PDF
- Type your question in the chat box
- Press Enter or click Send
- AI responds based on your PDF content
- Click page numbers to see references

### 4️⃣ Manage Documents
- View all documents in sidebar
- Click document to switch context
- Delete documents you don't need

---

## 💡 Example Questions

```
"What is this document about?"
"Summarize the key points"
"Explain the section on [topic]"
"List the main conclusions"
"What does page 5 say about [topic]?"
```

---

## 🔧 Troubleshooting

### Can't connect to backend?
✅ Check `VITE_API_URL` is set correctly  
✅ No trailing slash in URL  
✅ Redeploy after adding env vars

### Build failed?
✅ Base directory = `frontend`  
✅ Build command = `npm run build`  
✅ Publish directory = `frontend/dist`

### 404 on refresh?
✅ `netlify.toml` file is in root  
✅ Or add `_redirects` file in `frontend/public`

---

## 📊 Project Structure

```
Your Repository
├── frontend/              ← Deploy this folder
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── netlify.toml          ← Auto-config (already included)
└── NETLIFY_DEPLOYMENT_GUIDE.md
```

---

## 🌐 URLs

| Service | URL |
|---------|-----|
| Backend API | https://pdf-chatbot-kktm.onrender.com |
| API Docs | https://pdf-chatbot-kktm.onrender.com/docs |
| Your Frontend | https://[your-site].netlify.app |

---

## ✅ Deployment Checklist

- [ ] Fork/clone repository
- [ ] Connect to Netlify
- [ ] Set base directory to `frontend`
- [ ] Set build command to `npm run build`
- [ ] Set publish directory to `frontend/dist`
- [ ] Add environment variable `VITE_API_URL`
- [ ] Deploy!
- [ ] Test signup, upload, and chat

---

## 🎉 Success!

Your PDF ChatBot is now live and ready to use!

**Share your site:** `https://[your-site-name].netlify.app`

---

## 📞 Need Help?

- Check build logs in Netlify dashboard
- Review `NETLIFY_DEPLOYMENT_GUIDE.md` for detailed steps
- Verify backend is running: https://pdf-chatbot-kktm.onrender.com/docs
