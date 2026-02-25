import React from "react";

type Props = {
  onUploaded: (info: { documentId: string; filename: string }) => void;
  variant?: "sidebar" | "large";
};

const API_BASE = "http://localhost:5000/api/v1";

export const PdfUpload: React.FC<Props> = ({ onUploaded, variant = "sidebar" }) => {
  const [isUploading, setIsUploading] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Upload failed");
      }

      const data = await res.json();
      onUploaded({ documentId: data.document_id, filename: data.filename });
    } catch (error) {
      console.error(error);
      alert("Failed to upload PDF. Please try again.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  if (variant === "large") {
    return (
      <label className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 cursor-pointer transition-colors shadow-lg">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <span>{isUploading ? "Uploading..." : "Upload PDF"}</span>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={isUploading}
        />
      </label>
    );
  }

  return (
    <label className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-slate-600 hover:border-slate-500 hover:bg-slate-800/50 cursor-pointer transition-colors text-sm">
      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <span className="text-slate-300">{isUploading ? "Uploading..." : "Upload PDF"}</span>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={handleFileChange}
        disabled={isUploading}
      />
    </label>
  );
};

