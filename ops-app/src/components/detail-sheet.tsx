"use client";

import { useRef } from "react";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

// A row's full record, opened from its ID, so the tables stay one line per row.
export function DetailSheet({
  trigger,
  title,
  description,
  children,
}: {
  trigger: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
}) {
  const top = useRef<HTMLDivElement>(null); // open at the top, not at the first button
  return (
    <Sheet>
      <SheetTrigger className="cursor-pointer text-left font-mono text-sm font-semibold underline decoration-muted-foreground/40 underline-offset-4 hover:decoration-foreground">
        {trigger}
      </SheetTrigger>
      <SheetContent initialFocus={top} className="w-full overflow-y-auto data-[side=right]:w-full data-[side=right]:sm:max-w-xl">
        <SheetHeader ref={top} tabIndex={-1} className="border-b outline-none">
          <SheetTitle>{title}</SheetTitle>
          {description ? <SheetDescription>{description}</SheetDescription> : null}
        </SheetHeader>
        <div className="flex flex-col gap-6 p-6">{children}</div>
      </SheetContent>
    </Sheet>
  );
}

// Label and value pairs, read top to bottom like a load card in a TMS.
export function Facts({ items }: { items: [string, React.ReactNode][] }) {
  return (
    <dl className="grid grid-cols-[9rem_1fr] gap-x-4 gap-y-2 text-sm">
      {items.map(([name, value]) => (
        <div key={name} className="contents">
          <dt className="text-muted-foreground">{name}</dt>
          <dd className="min-w-0 break-words">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SheetSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
      {children}
    </section>
  );
}
