# 🚀 Netlify Deployment Guide - PDF ChatBot Frontend

## Quick Setup (5 Steps)

### Step 1: Build Settings
```
Base directory: frontend
Build command: npm run build
Publish directory: dist
```

### Step 2: Environment Variables
Add this environment variable:
```
Key: VITE_API_URL
Value: https://pdf-chatbot-kktm.onrender.com
```

### Step 3: Branch Configuration
```
Branch to deploy: main
```

### Step 4: Deploy
Click "Deploy site" and wait for build to complete (2-3 minutes)

### Step 5: Test Your Site
Once deployed, visit your Netlify URL and test:
1. Sign up with a new account
2. Upload a PDF
3. Ask questions about your PDF

---

## Complete Netlify Configuration

### Project Settings
| Setting | Value |
|---------|-------|
| **Project name** | pdf-chatbot (or your choice) |
| **Branch** | main |
| **Base directory** | `frontend` |
| **Build command** | `npm run build` |
| **Publish directory** | `dist` |
| **Functions directory** | (leave empty) |

### Environment Variables
Click "Add environment variables" and add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://pdf-chatbot-kktm.onrender.com` |

**Important:** No quotes needed in Netlify environment variables!

---

## Alternative: Manual Deploy

If you prefer to deploy manually:

### 1. Build Locally
```bash
cd frontend
npm install
npm run build
```

### 2. Deploy via Netlify CLI
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod --dir=frontend/dist
```

### 3. Set Environment Variable
After deployment, go to:
- Site settings → Environment variables
- Add `VITE_API_URL` = `https://pdf-chatbot-kktm.onrender.com`
- Trigger redeploy

---

## Troubleshooting

### Build Fails
**Error:** `Command failed with exit code 1`

**Solution:** Check these in order:
1. Ensure `Base directory` is set to `frontend`
2. Verify `Build command` is `npm run build`
3. Check `Publish directory` is `dist` (not `frontend/dist`)

### API Connection Issues
**Error:** Network errors or CORS issues

**Solution:**
1. Verify `VITE_API_URL` environment variable is set correctly
2. No trailing slash in the URL
3. Redeploy after adding environment variables

### 404 on Page Refresh
**Error:** Page not found when refreshing

**Solution:** Add a `_redirects` file (already included in your project):
```
/*    /index.html   200
```

### Build Takes Too Long
**Solution:** 
- First build takes 3-5 minutes (normal)
- Subsequent builds are faster (1-2 minutes)
- Check build logs for specific errors

---

## Post-Deployment Checklist

✅ Site is live and accessible  
✅ Environment variable `VITE_API_URL` is set  
✅ Can access login/signup page  
✅ Can create an account  
✅ Can upload a PDF  
✅ Can chat with uploaded PDF  
✅ Page refresh works (no 404)  

---

## Custom Domain (Optional)

### Add Custom Domain
1. Go to Site settings → Domain management
2. Click "Add custom domain"
3. Enter your domain (e.g., `chatbot.yourdomain.com`)
4. Follow DNS configuration instructions
5. Wait for SSL certificate (automatic, ~1 hour)

### Update Environment Variable
If using custom domain, update backend CORS settings to allow your domain.

---

## Performance Tips

### Enable Caching
Netlify automatically caches static assets. No configuration needed!

### Enable Compression
Already enabled by default (Brotli + Gzip)

### Analytics (Optional)
Enable Netlify Analytics in Site settings for visitor insights

---

## Continuous Deployment

Once set up, Netlify automatically:
- ✅ Deploys on every push to `main` branch
- ✅ Creates preview deployments for pull requests
- ✅ Runs build checks before deployment
- ✅ Rolls back on build failures

---

## Quick Reference

### Your URLs
- **Backend API:** https://pdf-chatbot-kktm.onrender.com
- **Frontend:** https://[your-site-name].netlify.app
- **API Docs:** https://pdf-chatbot-kktm.onrender.com/docs

### Support
- Netlify Docs: https://docs.netlify.com
- Build logs: Site → Deploys → [Latest deploy] → Deploy log
- Environment vars: Site settings → Environment variables

---

## 🎉 You're Done!

Your PDF ChatBot is now live! Share your Netlify URL with users.

**Example URL:** `https://pdf-chatbot-ai.netlify.app`
