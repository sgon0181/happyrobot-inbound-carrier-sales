"use client";

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar, type NavCounts } from "@/components/app-sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import Link from "next/link";
import { viewHref, type Scope, type View } from "@/lib/views";

export function AppShell({
  title,
  subtitle,
  view,
  scope,
  counts,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  view?: View;
  scope?: Scope;
  counts?: NavCounts;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar view={view} scope={scope} counts={counts} />
        <SidebarInset className="min-w-0 bg-muted/30">
          <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur lg:px-6">
            <SidebarTrigger />
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold">{title}</h1>
              {subtitle ? <p className="truncate text-xs text-muted-foreground">{subtitle}</p> : null}
            </div>
            {view !== "overview" && scope === "test" ? (
              <span className="rounded-full bg-status-act/12 px-2 py-0.5 text-xs font-medium text-status-act">Test calls</span>
            ) : null}
            <div className="ml-auto">{actions}</div>
          </header>
          <div className="mx-auto flex w-full max-w-[90rem] min-w-0 flex-1 flex-col gap-5 p-4 lg:p-6">
            {view !== "overview" && <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{scope === "test" ? "Test activity" : "Real activity"}</p>
                <p className="mt-1 text-xs text-muted-foreground">All recorded history{scope === "test" ? ". Excluded from business performance." : ". Test calls excluded."}</p>
              </div>
              <nav aria-label="Activity scope" className="flex gap-1 rounded-lg border bg-card p-1 text-sm">
                {(["real", "test"] as Scope[]).map((s) => (
                  <Link key={s} href={viewHref(view ?? "overview", s)} aria-current={(scope ?? "real") === s ? "page" : undefined} className={`rounded-md px-3 py-1.5 ${(scope ?? "real") === s ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted"}`}>
                    {s === "real" ? "Real calls" : "Test calls"}
                  </Link>
                ))}
              </nav>
            </div>}
            {children}
          </div>
        </SidebarInset>
      </SidebarProvider>
      <Toaster />
    </TooltipProvider>
  );
}
