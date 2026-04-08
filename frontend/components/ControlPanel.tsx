"use client";

interface Props {
  status: string;
  onGenerateNext: () => void;
  isLoading: boolean;
}

export default function ControlPanel({
  status,
  onGenerateNext,
  isLoading,
}: Props) {
  const canGenerate = status === "bible_ready" || status === "completed" || status === "error";

  return (
    <div className="flex gap-3">
      <button
        onClick={onGenerateNext}
        disabled={!canGenerate || isLoading}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
      >
        {isLoading ? "生成中..." : "生成下一章"}
      </button>
    </div>
  );
}
