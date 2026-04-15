import React from "react";
import ReactMarkdown from "react-markdown";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  selectedText?: string;
  pageNumber?: number;
};

type Props = {
  messages: Message[];
  onSend: (question: string) => void;
  isSending: boolean;
  currentSelection: { text: string; pageNumber: number } | null;
  onClearSelection: () => void;
};

export const ReadModeChat: React.FC<Props> = ({
  messages,
  onSend,
  isSending,
  currentSelection,
  onClearSelection,
}) => {
  const [inputValue, setInputValue] = React.useState("");
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || isSending) return;

    onSend(trimmed);
    setInputValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  return (
    <div className="flex flex-col h-full bg-[#111111]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/[0.06]">
        <h3 className="text-sm font-semibold text-slate-100">Reading Assistant</h3>
        <p className="text-xs text-slate-400 mt-0.5">Ask questions about selected text</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center">
              <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-medium text-slate-200 mb-1">Select text to get started</h4>
              <p className="text-xs text-slate-400 max-w-xs">
                Highlight any text in the PDF and click "Add to Chat" to ask questions about it.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                    />
                  </svg>
                </div>
              )}

              <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"} max-w-[80%]`}>
                {msg.role === "user" && msg.selectedText && (
                  <div className="mb-2 p-3 rounded-lg bg-[#1c1c1c] border border-white/[0.1] text-xs">
                    <div className="flex items-center gap-2 mb-1">
                      <svg className="w-3 h-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                        />
                      </svg>
                      <span className="text-indigo-400 font-medium">Page {msg.pageNumber} — Selected text:</span>
                    </div>
                    <p className="text-slate-300 italic line-clamp-3">"{msg.selectedText}"</p>
                  </div>
                )}

                <div
                  className={`rounded-2xl px-4 py-3 text-sm ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-[#161616] border border-white/[0.06] text-slate-200"
                  }`}
                >
                  <div className="prose prose-invert max-w-none text-sm leading-relaxed">
                    <ReactMarkdown
                      components={{
                        p: ({ node, ...props }) => <p className="mb-2 last:mb-0 whitespace-pre-wrap" {...props} />,
                        ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-1" {...props} />,
                        ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-1" {...props} />,
                        li: ({ node, ...props }) => <li className="text-sm leading-relaxed" {...props} />,
                        strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                        code: ({ node, ...props }) =>
                          node ? (
                            <code className="px-1.5 py-0.5 rounded bg-slate-900/70 text-xs" {...props} />
                          ) : (
                            <code className="block p-2 rounded bg-slate-900/80 text-xs overflow-x-auto" {...props} />
                          ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>

              {msg.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                  <svg className="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/[0.06]">
        {currentSelection && (
          <div className="mb-3 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <svg className="w-3 h-3 text-indigo-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                    />
                  </svg>
                  <span className="text-xs text-indigo-400 font-medium">Page {currentSelection.pageNumber} — Selected:</span>
                </div>
                <p className="text-xs text-slate-300 italic line-clamp-2">"{currentSelection.text}"</p>
              </div>
              <button
                onClick={onClearSelection}
                className="flex-shrink-0 p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200"
                aria-label="Clear selection"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end gap-2 bg-[#1c1c1c] border border-white/[0.1] rounded-xl px-4 py-3">
            <textarea
              ref={textareaRef}
              className="flex-1 bg-transparent outline-none text-sm text-slate-100 placeholder:text-slate-500 resize-none max-h-[200px] min-h-[32px]"
              placeholder="Ask about the selected text..."
              value={inputValue}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={isSending}
              rows={1}
            />
            <button
              type="submit"
              disabled={isSending || !inputValue.trim()}
              className="flex-shrink-0 p-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-700 disabled:cursor-not-allowed transition-colors"
              aria-label="Send message"
            >
              {isSending ? (
                <svg className="w-5 h-5 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
