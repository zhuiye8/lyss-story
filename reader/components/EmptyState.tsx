import Image from "next/image";
import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description: string;
  mascot?: "sad-pleading" | "thumbs-up" | "cheering" | "heart-love";
  actionLabel?: string;
  actionHref?: string;
}

export default function EmptyState({
  title,
  description,
  mascot = "sad-pleading",
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  return (
    <div className="relative w-full max-w-4xl mx-auto py-16 md:py-24 px-8 overflow-hidden rounded-3xl bg-surface-container-low">
      {/* Decorative blurs */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-32 -mt-32" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-secondary/5 rounded-full blur-3xl -ml-40 -mb-40" />

      <div className="relative flex flex-col md:flex-row items-center justify-between gap-8 md:gap-12">
        {/* Mascot */}
        <div className="w-full md:w-1/2 flex justify-center">
          <div className="relative w-48 h-48 md:w-64 md:h-64 floating">
            <Image
              src={`/mascot/lymo-${mascot}.png`}
              alt="Lymo"
              fill
              className="object-contain"
            />
          </div>
        </div>

        {/* Content */}
        <div className="w-full md:w-1/2 text-center md:text-left space-y-6">
          <div className="space-y-3">
            <h3 className="font-headline text-2xl md:text-3xl lg:text-4xl font-bold">
              {title}
            </h3>
            <p className="text-on-surface-variant font-body text-base md:text-lg leading-relaxed max-w-md mx-auto md:mx-0">
              {description}
            </p>
          </div>
          {actionLabel && actionHref && (
            <div className="flex flex-col sm:flex-row gap-3 justify-center md:justify-start">
              <Link
                href={actionHref}
                className="inline-flex items-center justify-center gap-2 bg-primary text-on-primary font-label text-sm font-semibold px-8 py-3.5 rounded-full hover:scale-105 transition-transform duration-300"
              >
                <span className="material-symbols-outlined text-lg">explore</span>
                {actionLabel}
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
