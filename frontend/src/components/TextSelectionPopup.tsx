import React from "react";

type Props = {
  position: { x: number; y: number };
  onAddToChat: () => void;
  onClose: () => void;
};

export const TextSelectionPopup: React.FC<Props> = ({ position, onAddToChat, onClose }) => {
  const popupRef = React.useRef<HTMLDivElement>(null);

  // Close popup when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={popupRef}
      className="fixed z-50 animate-in fade-in slide-in-from-top-2 duration-200"
      style={{
        left: `${position.x}px`,
        top: `${position.y - 60}px`,
        transform: "translateX(-50%)",
      }}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onAddToChat}
          className="flex items-center gap-2 px-4 py-2.5 hover:bg-slate-800 transition-colors text-sm font-medium text-slate-200 whitespace-nowrap"
        >
          <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          Add to Chat
        </button>
      </div>
      {/* Arrow pointing down */}
      <div
        className="absolute left-1/2 -translate-x-1/2 -bottom-2 w-0 h-0"
        style={{
          borderLeft: "8px solid transparent",
          borderRight: "8px solid transparent",
          borderTop: "8px solid rgb(51 65 85)", // slate-700
        }}
      />
    </div>
  );
};
