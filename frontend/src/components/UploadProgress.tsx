import React from "react";

type UploadingFile = {
  filename: string;
  progress: number;
};

type Props = {
  uploadingFiles: UploadingFile[];
  onCancel?: (filename: string) => void;
};

export const UploadProgress: React.FC<Props> = ({ uploadingFiles, onCancel }) => {
  if (uploadingFiles.length === 0) return null;

  const truncateFilename = (filename: string, maxLength: number = 20) => {
    if (filename.length <= maxLength) return filename;
    const extension = filename.split('.').pop();
    const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = nameWithoutExt.substring(0, maxLength - 3 - (extension?.length || 0));
    return `${truncatedName}...${extension}`;
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-2 mb-3">
      {uploadingFiles.map((file) => (
        <div
          key={file.filename}
          className="bg-slate-800/70 border border-slate-700 rounded-lg p-3 space-y-2"
        >
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center relative">
              <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <svg className="w-10 h-10 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate" title={file.filename}>
                {truncateFilename(file.filename)}
              </p>
              <p className="text-xs text-slate-400">
                {file.progress < 90 
                  ? `Uploading... ${file.progress}%` 
                  : file.progress < 100 
                    ? 'Processing on server...' 
                    : 'Finalizing...'}
              </p>
            </div>
            {onCancel && file.progress < 100 && (
              <button
                onClick={() => onCancel(file.filename)}
                className="flex-shrink-0 p-2 rounded-lg hover:bg-slate-700 transition-colors"
                aria-label="Cancel upload"
              >
                <svg className="w-4 h-4 text-slate-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300 ease-out"
              style={{ width: `${file.progress}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
