export function BookCardSkeleton() {
  return (
    <div className="flex gap-4 p-4 bg-surface-container-low rounded-xl">
      <div className="w-24 h-32 sm:w-28 sm:h-36 skeleton rounded-lg flex-shrink-0" />
      <div className="flex-1 space-y-3 py-1">
        <div className="h-5 w-3/4 skeleton rounded" />
        <div className="h-3 w-1/3 skeleton rounded-full" />
        <div className="space-y-2 mt-3">
          <div className="h-3 w-full skeleton rounded" />
          <div className="h-3 w-5/6 skeleton rounded" />
        </div>
        <div className="flex gap-4 mt-2">
          <div className="h-3 w-16 skeleton rounded-full" />
          <div className="h-3 w-16 skeleton rounded-full" />
        </div>
      </div>
    </div>
  );
}

export function BookshelfSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <BookCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="max-w-2xl mx-auto px-6 pt-20 space-y-6">
      <div className="h-8 w-2/3 skeleton rounded" />
      <div className="flex gap-3">
        <div className="h-6 w-16 skeleton rounded-full" />
        <div className="h-6 w-20 skeleton rounded-full" />
      </div>
      <div className="space-y-3 mt-6">
        <div className="h-4 w-full skeleton rounded" />
        <div className="h-4 w-full skeleton rounded" />
        <div className="h-4 w-3/4 skeleton rounded" />
      </div>
    </div>
  );
}

export function ChapterSkeleton() {
  return (
    <div className="max-w-2xl lg:max-w-3xl mx-auto px-6 pt-20 space-y-4">
      <div className="h-8 w-1/2 mx-auto skeleton rounded" />
      <div className="h-4 w-1/4 mx-auto skeleton rounded-full" />
      <div className="space-y-3 mt-8">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="h-4 skeleton rounded" style={{ width: `${75 + Math.random() * 25}%` }} />
        ))}
      </div>
    </div>
  );
}
