import React from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

// Configure PDF.js worker - use local file for reliability
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.mjs';

type Props = {
  pdfUrl: string;
  filename: string;
  onTextSelect: (selection: {
    text: string;
    pageNumber: number;
    position: { x: number; y: number };
  }) => void;
  currentPage: number;
  onPageChange: (page: number) => void;
};

export const ReadModePdfViewer: React.FC<Props> = ({
  pdfUrl,
  filename,
  onTextSelect,
  currentPage,
  onPageChange,
}) => {
  const [numPages, setNumPages] = React.useState<number>(0);
  const [scale, setScale] = React.useState(1.0);
  const [isLoading, setIsLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsLoading(false);
    setLoadError(null);
    console.log(`✅ PDF loaded successfully: ${numPages} pages`);
  };

  const onDocumentLoadError = (error: Error) => {
    console.error("❌ PDF load error:", error);
    setIsLoading(false);
    setLoadError(error.message || "Failed to load PDF");
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Get selection position for popup
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    onTextSelect({
      text: selectedText,
      pageNumber: currentPage,
      position: {
        x: rect.left + rect.width / 2,
        y: rect.top,
      },
    });
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 2.5));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < numPages) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#111111] border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
              clipRule="evenodd"
            />
          </svg>
          <h3 className="text-sm font-semibold text-slate-100 truncate max-w-xs" title={filename}>
            {filename}
          </h3>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom controls */}
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Zoom out"
            disabled={scale <= 0.5}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <span className="text-xs text-slate-400 w-12 text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Zoom in"
            disabled={scale >= 2.5}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
        </div>
      </div>

      {/* PDF Viewer */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto bg-[#0a0a0a] flex flex-col items-center py-4"
        onMouseUp={handleTextSelection}
      >
        {loadError ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-4 max-w-md">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-lg text-red-400 mb-2 font-semibold">Failed to load PDF</p>
              <p className="text-sm text-slate-400 mb-4">{loadError}</p>
              <p className="text-xs text-slate-500">
                The PDF file may be corrupted or incompatible. Try refreshing the page or uploading the document again.
              </p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-3">
              <svg className="w-12 h-12 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="text-sm text-slate-400">Loading PDF...</p>
            </div>
          </div>
        ) : null}

        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading={null}
          error={null}
        >
          {!isLoading && !loadError && (
            <Page
              pageNumber={currentPage}
              scale={scale}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="shadow-2xl"
            />
          )}
        </Document>
      </div>

      {/* Page navigation */}
      <div className="flex items-center justify-center gap-4 px-4 py-3 bg-[#111111] border-t border-white/[0.06]">
        <button
          onClick={handlePrevPage}
          disabled={currentPage <= 1}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex items-center gap-2">
          <input
            type="number"
            min={1}
            max={numPages}
            value={currentPage}
            onChange={(e) => {
              const page = parseInt(e.target.value);
              if (page >= 1 && page <= numPages) {
                onPageChange(page);
              }
            }}
            className="w-16 px-2 py-1 text-center bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          />
          <span className="text-sm text-slate-400">/ {numPages}</span>
        </div>

        <button
          onClick={handleNextPage}
          disabled={currentPage >= numPages}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};
