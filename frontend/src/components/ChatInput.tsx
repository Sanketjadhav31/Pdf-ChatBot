import React from "react";

type Props = {
  onSend: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
};

export const ChatInput: React.FC<Props> = ({ onSend, disabled, isLoading }) => {
  const [value, setValue] = React.useState("");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
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
    setValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="relative flex items-end gap-2 border border-slate-700 rounded-2xl px-4 py-3 bg-slate-800/50 shadow-lg focus-within:border-slate-600 transition-colors"
    >
      <textarea
        ref={textareaRef}
        className="flex-1 bg-transparent outline-none text-sm placeholder:text-slate-500 resize-none max-h-[200px] min-h-[24px]"
        placeholder="Message PDF Chatbot..."
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="flex-shrink-0 p-2 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 disabled:bg-slate-700 disabled:text-slate-500 transition-colors"
        aria-label="Send message"
      >
        {isLoading ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        )}
      </button>
    </form>
  );
};

