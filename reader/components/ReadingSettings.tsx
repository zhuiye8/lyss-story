"use client";

interface ReadingSettingsProps {
  open: boolean;
  onClose: () => void;
  fontSize: number;
  onFontSizeChange: (size: number) => void;
}

const themes = [
  { name: "极夜", bg: "#131313", text: "#e5e2e1", active: true },
  { name: "羊皮纸", bg: "#F4F1EA", text: "#3d3529" },
  { name: "青冥", bg: "#E8F0E8", text: "#2d3a2d" },
  { name: "远山", bg: "#E0E4EE", text: "#2d3040" },
];

export default function ReadingSettings({
  open,
  onClose,
  fontSize,
  onFontSizeChange,
}: ReadingSettingsProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full bg-surface/95 backdrop-blur-xl rounded-t-[2rem] p-6 pb-safe animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center mb-4">
          <div className="w-12 h-1.5 bg-surface-container-highest rounded-full" />
        </div>

        <div className="flex items-center justify-between mb-6">
          <h3 className="font-headline text-lg font-bold">阅读设置</h3>
          <span className="text-xs font-label text-on-surface-variant/40">v1.0</span>
        </div>

        <div className="space-y-6">
          {/* Font size */}
          <div>
            <p className="text-xs font-label text-on-surface-variant/60 uppercase tracking-widest mb-3">
              字号
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => onFontSizeChange(Math.max(14, fontSize - 2))}
                className="w-12 h-12 rounded-xl bg-surface-container-low flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors font-label text-sm"
              >
                Aa-
              </button>
              <div className="flex-1 text-center">
                <span className="font-label text-lg font-bold text-primary">{fontSize}</span>
              </div>
              <button
                onClick={() => onFontSizeChange(Math.min(28, fontSize + 2))}
                className="w-12 h-12 rounded-xl bg-surface-container-low flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors font-label text-sm"
              >
                Aa+
              </button>
            </div>
          </div>

          {/* Theme */}
          <div>
            <p className="text-xs font-label text-on-surface-variant/60 uppercase tracking-widest mb-3">
              主题
            </p>
            <div className="flex gap-4">
              {themes.map((theme) => (
                <button
                  key={theme.name}
                  className="flex flex-col items-center gap-2"
                  title={theme.name}
                >
                  <div
                    className={`w-10 h-10 rounded-full border-2 ${
                      theme.active
                        ? "border-primary ring-2 ring-primary/30 ring-offset-2 ring-offset-surface"
                        : "border-outline-variant/30"
                    }`}
                    style={{ backgroundColor: theme.bg }}
                  />
                  <span className="text-[10px] font-label text-on-surface-variant/60">
                    {theme.name}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Page mode */}
          <div>
            <p className="text-xs font-label text-on-surface-variant/60 uppercase tracking-widest mb-3">
              翻页模式
            </p>
            <div className="grid grid-cols-3 gap-2">
              {["平铺", "滚动", "无"].map((mode, i) => (
                <button
                  key={mode}
                  className={`py-2.5 rounded-xl font-label text-xs font-medium transition-colors ${
                    i === 1
                      ? "bg-primary text-on-primary"
                      : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-8 pt-4 border-t border-outline-variant/10">
          <button className="text-sm font-label text-on-surface-variant/60 hover:text-on-surface transition-colors">
            更多设置
          </button>
          <button
            onClick={onClose}
            className="bg-primary text-on-primary font-label text-sm font-semibold px-8 py-2.5 rounded-full hover:scale-105 transition-transform"
          >
            完成
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-up {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
