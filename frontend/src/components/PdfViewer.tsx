import React from "react";

type Props = {
  documentId: string;
  filename: string;
  initialPage?: number;
  onClose: () => void;
  authToken?: string;
};

export const PdfViewer: React.FC<Props> = ({ documentId, filename, initialPage, onClose, authToken }) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [pdfUrl, setPdfUrl] = React.useState<string>("");
  const [error, setError] = React.useState<string>("");

  React.useEffect(() => {
    const fetchPdf = async () => {
      try {
        setIsLoading(true);
        setError("");
        
        const response = await fetch(`http://localhost:5000/api/v1/documents/${documentId}/view`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        });

        if (!response.ok) {
          throw new Error(`Failed to load PDF: ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Add page parameter if specified
        const urlWithPage = initialPage 
          ? `${url}#page=${initialPage}&toolbar=1&navpanes=1&scrollbar=1`
          : `${url}#toolbar=1&navpanes=1&scrollbar=1`;
        
        setPdfUrl(urlWithPage);
      } catch (err) {
        console.error("Error loading PDF:", err);
        setError(err instanceof Error ? err.message : "Failed to load PDF");
      } finally {
        setIsLoading(false);
      }
    };

    fetchPdf();

    // Cleanup blob URL when component unmounts
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [documentId, initialPage, authToken]);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col border border-slate-700">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
            </svg>
            <h3 className="text-sm font-semibold text-slate-100 truncate">{filename}</h3>
            {initialPage && (
              <span className="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded">
                Page {initialPage}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            aria-label="Close viewer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-hidden bg-slate-950 relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950 z-10">
              <div className="flex flex-col items-center gap-3">
                <svg className="w-12 h-12 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <p className="text-sm text-slate-400">Loading PDF...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
              <div className="flex flex-col items-center gap-3 text-center px-4">
                <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-400">{error}</p>
                <button
                  onClick={onClose}
                  className="mt-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
          {pdfUrl && !error && (
            <iframe
              src={pdfUrl}
              className="w-full h-full"
              title={filename}
            />
          )}
        </div>
      </div>
    </div>
  );
};
