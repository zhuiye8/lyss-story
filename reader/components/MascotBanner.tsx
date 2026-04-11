import Image from "next/image";

export default function MascotBanner() {
  return (
    <section className="pb-6">
      <div className="w-full p-5 rounded-xl bg-surface-container-low border border-primary/10 flex items-center justify-between relative overflow-hidden group">
        <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="space-y-1 relative z-10">
          <p className="font-headline font-bold text-primary italic">狸灵寄语</p>
          <p className="text-on-surface-variant text-sm font-body">
            今日宜入梦，愿君遇良书
          </p>
        </div>
        <div className="relative z-10 w-14 h-14 flex-shrink-0">
          <Image
            src="/mascot/lymo-heart-love.png"
            alt="Lymo"
            width={56}
            height={56}
            className="object-contain"
          />
        </div>
      </div>
    </section>
  );
}
