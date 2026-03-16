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

const API_BASE = "http://localhost:5000/api/v1";

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

    // Process each file independently
    Array.from(files).forEach(file => {
      uploadFile(file);
    });

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
      await new Promise((resolve) => setTimeout(resolve, 400));
      onUploaded({ documentId: data.document_id, filename: data.filename });
      onUploadProgress?.(file.name, -1);
    } catch (error: any) {
      console.error(`❌ Upload failed:`, error);
      const message = error?.message || `Failed to upload ${file.name}. Please try again.`;
      alert(message);
      // Remove from uploading list on error
      onUploadProgress?.(file.name, -1);
    }
  };

  if (variant === "large") {
    return (
      <label className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 cursor-pointer transition-colors shadow-lg">
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
        />
      </>
    );
  }

  if (variant === "input") {
    return (
      <label className="cursor-pointer p-2 rounded-lg hover:bg-slate-700 transition-colors text-slate-400 hover:text-slate-200">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
        </svg>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
      </label>
    );
  }

  return (
    <label className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-slate-600 hover:border-slate-500 hover:bg-slate-800/50 cursor-pointer transition-colors text-sm">
      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <span className="text-slate-300">Upload PDF</span>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        multiple
        className="hidden"
        onChange={handleFileChange}
      />
    </label>
  );
};

