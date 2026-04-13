"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getChapterVersion,
  listChapterVersions,
  regenerateChapter,
  restoreChapterVersion,
} from "@/lib/api";
import type { ChapterVersionDetail, ChapterVersionSummary } from "@/types";

interface Props {
  storyId: string;
  chapterNum: number;
  onRegenerated?: () => void;
  onRestored?: () => void;
}

export default function ChapterVersionPanel({
  storyId,
  chapterNum,
  onRegenerated,
  onRestored,
}: Props) {
  const [versions, setVersions] = useState<ChapterVersionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [previewing, setPreviewing] = useState<ChapterVersionDetail | null>(null);

  const loadVersions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listChapterVersions(storyId, chapterNum);
      setVersions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [storyId, chapterNum]);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  const handleRegenerate = async () => {
    setSubmitting(true);
    setMessage(null);
    try {
      await regenerateChapter(storyId, chapterNum, feedback);
      setMessage("重写任务已启动，请在生成流程完成后刷新页面查看新版本");
      setShowDialog(false);
      setFeedback("");
      onRegenerated?.();
    } catch (e) {
      setMessage(`启动失败：${(e as Error).message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreview = async (versionId: number) => {
    try {
      const detail = await getChapterVersion(storyId, chapterNum, versionId);
      setPreviewing(detail);
    } catch (e) {
      setMessage(`加载版本失败：${(e as Error).message}`);
    }
  };

  const handleRestore = async (versionId: number, versionNum: number) => {
    if (!confirm(`确认回滚到第 ${versionNum} 版？当前版本会先被保存为新的历史版本。`)) {
      return;
    }
    try {
      await restoreChapterVersion(storyId, chapterNum, versionId);
      setMessage(`已回滚到第 ${versionNum} 版`);
      setPreviewing(null);
      await loadVersions();
      onRestored?.();
    } catch (e) {
      setMessage(`回滚失败：${(e as Error).message}`);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">版本与重写</h3>
        <button
          onClick={() => setShowDialog(true)}
          className="px-3 py-1.5 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded transition"
        >
          重新生成
        </button>
      </div>

      {message && (
        <div className="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
          {message}
        </div>
      )}

      <div className="space-y-2">
        <p className="text-xs text-gray-500">
          {loading ? "加载历史..." : `共 ${versions.length} 个历史版本`}
        </p>
        {versions.length > 0 && (
          <ul className="space-y-1.5 max-h-56 overflow-y-auto">
            {versions.map((v) => (
              <li
                key={v.id}
                className="flex items-center justify-between gap-3 px-3 py-2 bg-white border rounded text-sm"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-800">
                      v{v.version_num}
                    </span>
                    <span className="text-gray-500 truncate">
                      {v.title || "(无标题)"}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5 truncate">
                    {v.word_count} 字 · {new Date(v.created_at).toLocaleString("zh-CN")}
                    {v.feedback && ` · 反馈：${v.feedback.slice(0, 40)}`}
                  </div>
                </div>
                <div className="flex gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => handlePreview(v.id)}
                    className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
                  >
                    预览
                  </button>
                  <button
                    onClick={() => handleRestore(v.id, v.version_num)}
                    className="px-2 py-1 text-xs text-amber-700 hover:bg-amber-50 rounded"
                  >
                    回滚
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Regenerate dialog */}
      {showDialog && (
        <div
          className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
          onClick={() => !submitting && setShowDialog(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-bold mb-3">重新生成第 {chapterNum} 章</h2>
            <p className="text-sm text-gray-600 mb-3">
              提供具体反馈，Writer 会根据反馈改写（情节大方向不变）。留空则无反馈重写。
            </p>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="例如：主角对话太生硬；节奏过快；想加一段内心独白..."
              rows={6}
              className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              disabled={submitting}
            />
            <p className="text-xs text-gray-500 mt-2">
              当前版本将自动存入历史记录，可随时回滚。
            </p>
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setShowDialog(false)}
                disabled={submitting}
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleRegenerate}
                disabled={submitting}
                className="px-4 py-2 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded disabled:opacity-50"
              >
                {submitting ? "提交中..." : "开始重写"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview dialog */}
      {previewing && (
        <div
          className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
          onClick={() => setPreviewing(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-5 border-b flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold">
                  v{previewing.version_num} {previewing.title && `· ${previewing.title}`}
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {previewing.word_count} 字 · {new Date(previewing.created_at).toLocaleString("zh-CN")}
                </p>
                {previewing.feedback && (
                  <p className="text-xs text-amber-700 mt-1">
                    反馈：{previewing.feedback}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleRestore(previewing.id, previewing.version_num)}
                  className="px-3 py-1.5 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded"
                >
                  回滚到此版本
                </button>
                <button
                  onClick={() => setPreviewing(null)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                >
                  关闭
                </button>
              </div>
            </div>
            <div
              className="p-5 overflow-y-auto text-sm leading-8 text-gray-800"
              style={{
                fontFamily: '"Noto Serif SC", "Source Han Serif SC", serif',
              }}
            >
              {previewing.content.split("\n").filter((p) => p.trim()).map((p, i) =>
                p.trim() === "***" ? (
                  <hr key={i} className="my-6 border-gray-300" />
                ) : (
                  <p key={i} className="indent-8 mb-3 text-justify">{p}</p>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
