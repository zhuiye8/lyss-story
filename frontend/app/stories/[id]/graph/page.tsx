"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy route — the old 5-tab visualization page has been split into
 * /characters, /world, /insights, /pipeline, /versions, and /galaxy.
 * Redirect to the new insights page by default.
 */
export default function LegacyGraphPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const router = useRouter();
  useEffect(() => {
    router.replace(`/stories/${storyId}/insights`);
  }, [router, storyId]);
  return null;
}
