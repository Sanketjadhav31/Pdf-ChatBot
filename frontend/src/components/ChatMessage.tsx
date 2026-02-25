import React from "react";

export type ChatRole = "user" | "assistant";

type Props = {
  role: ChatRole;
  content: string;
  references?: {
    documentId: string;
    pageNumber: number;
    documentHeading?: string | null;
    paragraphHeading?: string | null;
  }[];
};

export const ChatMessage: React.FC<Props> = ({
  role,
  content,
  references = [],
}) => {
  const isUser = role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
      )}
      
      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[75%]`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm ${
            isUser
              ? "bg-indigo-600 text-white"
              : "bg-slate-800 text-slate-50"
          }`}
        >
          <p className="whitespace-pre-wrap leading-relaxed">{content}</p>

          {!isUser && references.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                References
              </div>
              {references.map((ref, idx) => (
                <div 
                  key={`${ref.documentId}-${ref.pageNumber}-${idx}`}
                  className="text-xs bg-slate-900/50 rounded-lg p-2 space-y-1"
                >
                  {ref.documentHeading && (
                    <div className="text-slate-300">
                      <span className="text-slate-500">Document:</span> {ref.documentHeading}
                    </div>
                  )}
                  {ref.paragraphHeading && (
                    <div className="text-slate-300">
                      <span className="text-slate-500">Section:</span> {ref.paragraphHeading}
                    </div>
                  )}
                  <div className="text-slate-400">
                    <span className="text-slate-500">Page:</span> {ref.pageNumber}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
          <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
    </div>
  );
};

