"use client";

interface Props {
  status: string;
  currentChapter: number | null;
  errorMessage: string | null;
}

export default function GenerationStatus({
  status,
  currentChapter,
  errorMessage,
}: Props) {
  const statusMap: Record<string, { label: string; color: string }> = {
    initializing: { label: "初始化中...", color: "bg-blue-500" },
    bible_ready: { label: "就绪", color: "bg-green-500" },
    generating: { label: `生成第${currentChapter}章中...`, color: "bg-yellow-500" },
    error: { label: "错误", color: "bg-red-500" },
    completed: { label: "已完成", color: "bg-green-600" },
  };

  const info = statusMap[status] || { label: status, color: "bg-gray-500" };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <span className={`w-3 h-3 rounded-full ${info.color} ${status === "generating" || status === "initializing" ? "animate-pulse" : ""}`} />
      <span className="text-sm font-medium">{info.label}</span>
      {errorMessage && (
        <span className="text-sm text-red-600 ml-2">{errorMessage}</span>
      )}
    </div>
  );
}
