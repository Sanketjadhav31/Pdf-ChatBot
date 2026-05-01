import React from "react";
import ReactMarkdown from "react-markdown";

export type ChatRole = "user" | "assistant";

type Reference = {
  documentId: string;
  pageNumber: number;
  documentHeading?: string | null;
  paragraphHeading?: string | null;
  snippet?: string | null;
  snippetHover?: string | null;
};

type UploadedDocument = {
  documentId: string;
  filename: string;
  uploadedAt: Date;
};

type AttachedDoc = {
  documentId: string;
  filename: string;
};

type Props = {
  role: ChatRole;
  content: string;
  attachedDocs?: AttachedDoc[];
  references?: Reference[];
  onViewReference?: (documentId: string, pageNumber: number) => void;
  onOpenDocument?: (documentId: string) => void;
  uploadedDocs?: UploadedDocument[];
  thinkingSteps?: string[];  // New: Array of thinking steps
  isThinking?: boolean;  // New: Whether still thinking
};

export const ChatMessage: React.FC<Props> = ({
  role,
  content,
  attachedDocs = [],
  references = [],
  onViewReference,
  onOpenDocument,
  uploadedDocs = [],
  thinkingSteps = [],
  isThinking = false,
}) => {
  const isUser = role === "user";

  const [sourcesExpanded, setSourcesExpanded] = React.useState(false);
  const [expandedRefKey, setExpandedRefKey] = React.useState<string | null>(null);
  const [thinkingExpanded, setThinkingExpanded] = React.useState(true);  // Auto-expand thinking

  React.useEffect(() => {
    if (!sourcesExpanded) {
      setExpandedRefKey(null);
    }
  }, [sourcesExpanded]);

  // Get filename from document ID
  const getFilename = (documentId: string) => {
    const doc = uploadedDocs.find(d => d.documentId === documentId);
    return doc?.filename || documentId;
  };

  const normalizeSnippet = (t: string) => t.replace(/\s+/g, " ").trim();

  const extractHeaderToStrip = (snippets: string[]) => {
    const cleaned = snippets.map(normalizeSnippet).filter(Boolean);
    if (cleaned.length === 0) return "";
    if (cleaned.length < 2) return "";

    const prefixLen = 30;
    const firstPrefixes = cleaned.map((s) => s.slice(0, prefixLen));
    const counts: Record<string, number> = {};
    for (const p of firstPrefixes) {
      if (!p) continue;
      counts[p] = (counts[p] || 0) + 1;
    }

    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    if (entries.length === 0) return "";

    const [topPrefix, topCount] = entries[0];
    const requiredCount = Math.ceil(cleaned.length * 0.5);
    if (topCount < requiredCount) return "";

    // Common header phrase heuristic: many PDFs repeat a header ending with "years".
    const sample = cleaned.find((s) => s.startsWith(topPrefix)) || cleaned[0];
    const sampleLower = sample.toLowerCase();
    const yearsIdx = sampleLower.indexOf("years");
    if (yearsIdx !== -1) {
      const candidate = sample.slice(0, yearsIdx + "years".length).trim();
      const candidateCount = cleaned.filter((s) =>
        s.toLowerCase().startsWith(candidate.toLowerCase())
      ).length;
      if (candidateCount >= requiredCount) return candidate;
    }

    return topPrefix;
  };

  const cleanEvidenceSnippet = (
    raw: string | null | undefined,
    headerToStrip: string
  ) => {
    let t = normalizeSnippet(raw || "");
    if (!t) return "";

    if (headerToStrip) {
      const tLower = t.toLowerCase();
      const headerLower = headerToStrip.toLowerCase();
      if (tLower.startsWith(headerLower)) {
        t = t.slice(headerToStrip.length).trim();
      }
    }

    // Remove leftover separators/quotes after stripping headers.
    t = t.replace(/^["“”'’]+/, "").trim();
    t = t.replace(/^[-–—:•\s]+/, "").trim();

    // Prefer showing the first 1-2 sentences (usually the evidence sentence).
    const sentences = t.match(/[^.!?]+[.!?]+/g) || [];
    if (sentences.length > 0) {
      return normalizeSnippet(sentences.slice(0, 2).join(" "));
    }

    return t;
  };

  // Group references by document
  const groupedReferences = React.useMemo(() => {
    const groups: Record<string, Reference[]> = {};
    references.forEach((ref) => {
      const key = ref.documentId;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(ref);
    });
    return groups;
  }, [references]);

  return (
    <div className={`flex gap-4 msg-enter ${isUser ? "justify-end" : "justify-start"}`}>
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
            isUser ? "msg-user" : "msg-bot"
          }`}
        >
          {isUser && attachedDocs.length > 0 && (
            <div className="mb-3 space-y-2">
              {attachedDocs.map((doc) => (
                <button
                  key={doc.documentId}
                  type="button"
                  onClick={() => onOpenDocument?.(doc.documentId)}
                  className="w-full text-left flex items-center gap-3 p-3 rounded-xl bg-white/10 border border-white/15 hover:bg-white/15 transition-colors"
                  title={doc.filename}
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/15 flex items-center justify-center">
                    <svg className="w-5 h-5 text-red-300" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-white truncate">{doc.filename}</div>
                    <div className="text-xs text-white/70">PDF</div>
                  </div>
                </button>
              ))}
            </div>
          )}
          <div className="prose prose-invert max-w-none text-sm leading-relaxed">
            {/* Thinking Section - Only show if we have actual thinking steps (not just status) */}
            {!isUser && thinkingSteps.length > 0 && (
              <div className="mb-3 rounded-lg border border-slate-700/50 bg-slate-900/30 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setThinkingExpanded((v) => !v)}
                  className="w-full flex items-center justify-between gap-3 p-3 cursor-pointer select-none hover:bg-slate-800/30 transition-colors"
                  aria-expanded={thinkingExpanded}
                >
                  <div className="flex items-center gap-2">
                    {isThinking ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-sm font-medium text-indigo-300">Thinking...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        <span className="text-sm font-medium text-slate-300">Thought process</span>
                      </div>
                    )}
                  </div>

                  <svg
                    className={`w-4 h-4 text-slate-400 transition-transform ${thinkingExpanded ? "rotate-180" : "rotate-0"}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {thinkingExpanded && (
                  <div className="px-3 pb-3 max-h-60 overflow-y-auto">
                    <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {thinkingSteps.map((step, idx) => (
                        <div key={idx} className="mb-2 last:mb-0">
                          {step}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <ReactMarkdown
              components={{
                h1: ({ node, ...props }) => (
                  <h1
                    className="text-lg font-semibold text-slate-50 border-b border-white/10 pb-1 mb-2"
                    {...props}
                  />
                ),
                h2: ({ node, ...props }) => (
                  <h2
                    className="text-base font-semibold text-slate-50 border-b border-white/10 pb-1 mb-2"
                    {...props}
                  />
                ),
                h3: ({ node, ...props }) => (
                  <h3
                    className="text-sm font-semibold text-slate-50 mb-1"
                    {...props}
                  />
                ),
                strong: ({ node, ...props }) => (
                  <strong className="font-semibold text-slate-50" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-inside space-y-1 text-slate-100" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal list-inside space-y-1 text-slate-100" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="text-sm leading-relaxed" {...props} />
                ),
                p: ({ node, ...props }) => (
                  <p className="mb-2 last:mb-0 whitespace-pre-wrap" {...props} />
                ),
                code: ({ node,  ...props }) =>
                  node ? (
                    <code
                      className="px-1.5 py-0.5 rounded bg-slate-900/70 text-[0.8rem] text-indigo-200"
                      {...props}
                    />
                  ) : (
                    <code
                      className="block p-2 rounded bg-slate-900/80 text-xs text-indigo-100 overflow-x-auto"
                      {...props}
                    />
                  ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {!isUser && references.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <button
                type="button"
                onClick={() => setSourcesExpanded((v) => !v)}
                className="w-full flex items-center justify-between gap-3 cursor-pointer select-none"
                aria-expanded={sourcesExpanded}
              >
                <div className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-xs font-medium text-slate-300 uppercase tracking-wide">
                    Sources ({references.length})
                  </span>
                </div>

                <svg
                  className={`w-4 h-4 text-slate-400 transition-transform ${sourcesExpanded ? "rotate-180" : "rotate-0"}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {sourcesExpanded && (
                <div className="mt-3 space-y-3">
                  {Object.entries(groupedReferences).map(([documentId, refs], idx) => {
                    const filename = getFilename(documentId);
                    const headerToStrip = extractHeaderToStrip(
                      refs.map((r) => r.snippet || "").filter(Boolean)
                    );

                    return (
                      <div
                        key={`${documentId}-${idx}`}
                        className="bg-slate-900/35 rounded-md border border-slate-700/40 overflow-hidden"
                      >
                        <div className="p-2 flex items-center justify-between gap-2 border-b border-slate-700/30">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className="w-4 h-4 rounded bg-red-500/10 flex items-center justify-center flex-shrink-0">
                              <svg className="w-2.5 h-2.5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            </div>
                            <p className="text-xs font-medium text-slate-200 truncate" title={filename}>
                              {filename}
                            </p>
                          </div>
                        </div>

                        <div className="p-2 space-y-2">
                          {refs.map((ref, refIdx) => {
                            const refKey = `${documentId}-ref-${ref.pageNumber}-${refIdx}`;
                            const isExpanded = expandedRefKey === refKey;

                            const displaySnippet = cleanEvidenceSnippet(ref.snippet, headerToStrip);
                            const displaySnippetHover = cleanEvidenceSnippet(
                              ref.snippetHover || ref.snippet,
                              headerToStrip
                            );

                            return (
                              <div
                                key={refKey}
                                className="rounded-md border border-slate-700/50 bg-slate-900/25 transition-all"
                              >
                                <button
                                  type="button"
                                  onClick={() =>
                                    setExpandedRefKey((prev) =>
                                      prev === refKey ? null : refKey
                                    )
                                  }
                                  className="w-full text-left p-2 flex items-start justify-between gap-3 hover:border-indigo-500/30 transition-colors"
                                  aria-expanded={isExpanded}
                                >
                                  <div className="min-w-0 pr-1">
                                    <div className="flex items-center gap-2 flex-wrap mb-1">
                                      <span className="text-[0.68rem] uppercase font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                                        Page {ref.pageNumber}
                                      </span>
                                    </div>

                                    {isExpanded && displaySnippet && (
                                      <div
                                        className="text-[0.78rem] text-slate-300 leading-snug overflow-hidden"
                                        style={{
                                          display: "-webkit-box",
                                          WebkitLineClamp: 3,
                                          WebkitBoxOrient: "vertical",
                                        }}
                                        title={displaySnippet}
                                      >
                                        &ldquo;{displaySnippet}&rdquo;
                                      </div>
                                    )}
                                  </div>

                                  <svg
                                    className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? "rotate-180" : "rotate-0"}`}
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    aria-hidden="true"
                                  >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 18l6-6-6-6" />
                                  </svg>
                                </button>

                                {isExpanded && (
                                  <div className="px-2 pb-2">
                                    {displaySnippetHover &&
                                      displaySnippetHover !== displaySnippet && (
                                        <div
                                          className="text-[0.74rem] text-slate-400 leading-snug overflow-hidden mb-2"
                                          style={{
                                            display: "-webkit-box",
                                            WebkitLineClamp: 2,
                                            WebkitBoxOrient: "vertical",
                                          }}
                                          title={displaySnippetHover}
                                        >
                                          {displaySnippetHover}
                                        </div>
                                      )}

                                    <div className="flex justify-end">
                                      <button
                                        type="button"
                                        onClick={() => onViewReference?.(documentId, ref.pageNumber)}
                                        className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/20 hover:border-indigo-500/40 text-xs text-indigo-200 transition-colors"
                                        title={`Open ${filename} (page ${ref.pageNumber})`}
                                      >
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.5 12h3m13 0h3M12 2.5v3m0 13v3" />
                                        </svg>
                                        Open in PDF
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
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