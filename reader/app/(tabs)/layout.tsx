import BottomNav from "@/components/BottomNav";

export default function TabsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen pb-20 lg:pb-0">
      {children}
      <BottomNav />
    </div>
  );
}
