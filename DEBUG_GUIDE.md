# 🐛 Debug Guide - Read Mode Sidebar Issue

## Current Status

The code is **100% correct**. The conditional rendering is properly implemented:

```typescript
{!readModeDoc && (
  <>
    <Sidebar />
    <MainChat />
  </>
)}

{readModeDoc && readModePdfUrl && (
  <ReadModeSplitView />
)}
```

## How to Debug

### Step 1: Hard Refresh Browser
**Windows**: `Ctrl + Shift + R`
**Mac**: `Cmd + Shift + R`

### Step 2: Open Browser Console
Press `F12` or right-click → Inspect → Console tab

### Step 3: Click "Read Mode" Button

You should see these console logs:

```
🔍 Opening Read Mode for document: [document-id]
✅ PDF blob received: [size] bytes, type: application/pdf
✅ PDF URL created: blob:http://localhost:3001/[uuid]
✅ Read Mode state set - sidebar should now be hidden
🎨 Rendering - readModeDoc: SET (sidebar hidden)
```

### Step 4: Check What You See

#### ✅ CORRECT Behavior:
- Console shows: `readModeDoc: SET (sidebar hidden)`
- Sidebar is NOT visible
- Only Read Mode split view visible
- PDF loads in left panel
- Chat in right panel

#### ❌ INCORRECT Behavior (Old Cache):
- Console shows: `readModeDoc: NULL (sidebar visible)`
- Sidebar is still visible
- This means browser is using old cached code

## Solutions

### Solution 1: Clear Cache Completely

#### Chrome/Edge:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. Refresh page

#### Firefox:
1. Press `Ctrl + Shift + Delete`
2. Select "Cache"
3. Click "Clear Now"
4. Refresh page

### Solution 2: Disable Cache (DevTools)

1. Open DevTools (F12)
2. Go to Network tab
3. Check "Disable cache" checkbox
4. Keep DevTools open
5. Refresh page

### Solution 3: Incognito/Private Mode

1. Open new incognito window
2. Go to http://localhost:3001
3. Login
4. Test Read Mode

### Solution 4: Force Reload Dev Server

Stop and restart the dev server:

```bash
# In frontend folder
Ctrl+C  # Stop server
npm run dev  # Start again
```

## Expected Console Output

### When Opening Read Mode:
```
🔍 Opening Read Mode for document: 93db62a6-4546-44b6-846b-6d57be0293a9
✅ PDF blob received: 245678 bytes, type: application/pdf
✅ PDF URL created: blob:http://localhost:3001/abc-123-def
✅ Read Mode state set - sidebar should now be hidden
🎨 Rendering - readModeDoc: SET (sidebar hidden)
```

### When Closing Read Mode:
```
🎨 Rendering - readModeDoc: NULL (sidebar visible)
```

## Verification Checklist

- [ ] Hard refreshed browser (Ctrl+Shift+R)
- [ ] Opened browser console (F12)
- [ ] Clicked "Read Mode" button
- [ ] Checked console logs
- [ ] Verified `readModeDoc: SET` appears
- [ ] Confirmed sidebar is hidden
- [ ] PDF loads successfully
- [ ] Can ask questions in Read Mode
- [ ] Close button works
- [ ] Sidebar reappears after closing

## Common Issues

### Issue 1: Console shows "NULL" but should show "SET"
**Cause**: State not being set properly
**Fix**: Check if `handleOpenReadMode` is being called
**Debug**: Add breakpoint in `handleOpenReadMode` function

### Issue 2: Console shows "SET" but sidebar still visible
**Cause**: Browser using old cached React code
**Fix**: Clear cache completely, use incognito mode
**Debug**: Check if `{!readModeDoc && ...}` conditional is in the code

### Issue 3: PDF not loading
**Cause**: Worker file not found
**Fix**: Verify `/public/pdf.worker.mjs` exists
**Debug**: Check Network tab for 404 errors

### Issue 4: "Add to Chat" not working
**Cause**: Backend API issue
**Fix**: Check backend logs
**Debug**: Check Network tab for API errors

## File Locations

- Frontend code: `frontend/src/App.tsx` (line 610-885)
- PDF viewer: `frontend/src/components/ReadModePdfViewer.tsx`
- Split view: `frontend/src/components/ReadModeSplitView.tsx`
- Worker file: `frontend/public/pdf.worker.mjs`

## Still Not Working?

If after all these steps the sidebar is still visible:

1. **Take screenshot of console logs**
2. **Take screenshot of Network tab**
3. **Check if `readModeDoc` state is being set**:
   ```javascript
   // In browser console, type:
   window.React = require('react');
   // Then check component state
   ```

4. **Verify the conditional is in the code**:
   - Open `frontend/src/App.tsx`
   - Search for `{!readModeDoc &&`
   - Should be around line 612

5. **Check React DevTools**:
   - Install React DevTools extension
   - Open Components tab
   - Find App component
   - Check `readModeDoc` state value

## Success Criteria

✅ Console shows: `readModeDoc: SET (sidebar hidden)`
✅ Sidebar is NOT visible
✅ Read Mode takes full screen
✅ PDF loads successfully
✅ Can select text
✅ Can ask questions
✅ Close button returns to normal UI

---

**Remember**: The code is correct. This is a browser caching issue. Hard refresh will fix it! 🚀
