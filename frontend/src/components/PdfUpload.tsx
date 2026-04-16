import React from "react";

type Props = {
  onUploaded: (info: { documentId: string; filename: string }) => void;
  onUploadStart?: (filename: string) => void;
  onUploadProgress?: (filename: string, progress: number) => void;
  variant?: "sidebar" | "large" | "input" | "hidden";
  /** Ref to expose triggerUpload() so other components can trigger the same file input */
  uploadTriggerRef?: React.MutableRefObject<(() => void) | null>;
  authToken?: string | null;
};

const API_BASE = import.meta.env.VITE_API_URL;

export const PdfUpload: React.FC<Props> = ({
  onUploaded,
  onUploadStart,
  onUploadProgress,
  variant = "sidebar",
  uploadTriggerRef,
  authToken,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  React.useEffect(() => {
    if (uploadTriggerRef) {
      uploadTriggerRef.current = () => fileInputRef.current?.click();
      return () => { uploadTriggerRef.current = null; };
    }
  }, [uploadTriggerRef]);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Upload sequentially to avoid hammering the backend (Mongo/GridFS + embeddings)
    // with too many concurrent PDF processing jobs.
    for (const file of Array.from(files)) {
      await uploadFile(file);
    }

    // Reset input to allow uploading the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadFile = async (file: File) => {
    console.log(`📤 Starting upload: ${file.name}`);
    onUploadStart?.(file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          console.log(`📊 Upload progress: ${percentComplete}%`);
          onUploadProgress?.(file.name, percentComplete);
        }
      });

      const uploadPromise = new Promise<any>((resolve, reject) => {
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            console.error(`❌ Upload failed with status: ${xhr.status}`);
            let message = `Upload failed (${xhr.status})`;
            try {
              const data = JSON.parse(xhr.responseText);
              if (data?.detail) {
                message = data.detail;
              }
            } catch {
              // ignore JSON parse error and keep default message
            }
            reject(new Error(message));
          }
        });

        xhr.addEventListener("error", () => {
          console.error(`❌ Upload error occurred`);
          reject(new Error("Upload failed"));
        });
        
        xhr.addEventListener("abort", () => {
          console.error(`❌ Upload cancelled`);
          reject(new Error("Upload cancelled"));
        });

        xhr.open("POST", `${API_BASE}/documents/upload`);
        if (authToken) {
          xhr.setRequestHeader("Authorization", `Bearer ${authToken}`);
        }
        xhr.send(formData);
      });

      const data = await uploadPromise;
      console.log(`✨ Document processed:`, data);

      // Ensure we show 100% once server responds, then mark upload complete
      onUploadProgress?.(file.name, 100);
      // Small delay only; large per-file delays stack up when uploading many PDFs.
      await new Promise((resolve) => setTimeout(resolve, 50));
      onUploaded({ documentId: data.document_id, filename: data.filename });
      onUploadProgress?.(file.name, -1);
    } catch (error: any) {
      console.error(`❌ Upload failed:`, error);
      
      // Extract meaningful error message
      let message = error?.message || `Failed to upload ${file.name}. Please try again.`;
      
      // Format multi-line error messages for better display
      if (message.includes('\n')) {
        // For multi-line messages (like image-based PDF errors), show in alert with proper formatting
        alert(`Upload Failed\n\n${message}`);
      } else {
        // For single-line messages, show as-is
        alert(message);
      }
      
      // Remove from uploading list on error
      onUploadProgress?.(file.name, -1);
    }
  };

  if (variant === "large") {
    return (
      <label 
        className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 cursor-pointer transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95"
        title="Upload one or more PDF files (Ctrl+U)"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <span>Upload PDF</span>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
          aria-label="Upload PDF files"
        />
      </label>
    );
  }

  if (variant === "hidden") {
    return (
      <>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="sr-only"
          onChange={handleFileChange}
          aria-hidden
          aria-label="Upload PDF files"
        />
      </>
    );
  }

  if (variant === "input") {
    return (
      <label 
        className="cursor-pointer p-2 rounded-lg hover:bg-slate-700 transition-all text-slate-400 hover:text-slate-200 hover:scale-110 active:scale-95 relative group"
        title="Attach PDF files (Ctrl+U)"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
        </svg>
        {/* Tooltip */}
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg border border-slate-700">
          Attach PDF files
          <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></span>
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
          aria-label="Attach PDF files"
        />
      </label>
    );
  }

  return (
    <label 
      className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-slate-600 hover:border-indigo-500 hover:bg-slate-800/50 cursor-pointer transition-all text-sm hover:shadow-md group"
      title="Click to upload PDF files or drag and drop"
    >
      <svg className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <span className="text-slate-300 group-hover:text-indigo-300 transition-colors">Upload PDF</span>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        multiple
        className="hidden"
        onChange={handleFileChange}
        aria-label="Upload PDF files"
      />
    </label>
  );
};

