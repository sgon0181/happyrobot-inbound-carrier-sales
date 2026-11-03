"use client";

import Link from "next/link";
import {
  IconFilter,
  IconHandStop,
  IconLayoutDashboard,
  IconMapPin,
  IconPhoneCall,
  IconTruckDelivery,
} from "@tabler/icons-react";

import logo from "@/brand-assets/blacklogo.png";
import icon from "@/brand-assets/blackicon.png";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { VIEW_TITLE, viewHref, type Scope, type View } from "@/lib/views";

const ICON: Record<View, React.ReactNode> = {
  overview: <IconLayoutDashboard />,
  reservations: <IconHandStop />,
  bookings: <IconTruckDelivery />,
  calls: <IconPhoneCall />,
  demand: <IconMapPin />,
};

export type NavCounts = Partial<Record<View, number>>;

export function AppSidebar({ view, scope, counts = {} }: { view?: View; scope?: Scope; counts?: NavCounts }) {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const shown: Scope = scope ?? "real";

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-16 justify-center">
        <Link
          href="/"
          className="flex h-10 w-full items-center justify-start pl-2.5 pr-3 group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-1!"
        >
          {collapsed ? (
            <img src={icon.src} alt="HappyRobot" className="size-7 shrink-0 object-contain" />
          ) : (
            <img src={logo.src} alt="HappyRobot" className="h-5 w-auto max-w-full object-contain object-left" />
          )}
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="pt-4">
          <SidebarGroupLabel>Carrier sales</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {(Object.keys(VIEW_TITLE) as View[]).map((v) => (
                <SidebarMenuItem key={v}>
                  <SidebarMenuButton isActive={(view ?? "overview") === v} tooltip={VIEW_TITLE[v]} render={<Link href={viewHref(v, shown)} />}>
                    {ICON[v]}
                    <span>{VIEW_TITLE[v]}</span>
                  </SidebarMenuButton>
                  {counts[v] ? <SidebarMenuBadge className="tabular-nums">{counts[v]}</SidebarMenuBadge> : null}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup className="mt-auto pb-4 group-data-[collapsible=icon]:hidden">
          <SidebarGroupLabel>
            <IconFilter className="mr-1 size-3.5" /> Calls shown
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <div className="grid grid-cols-2 rounded-lg bg-sidebar-accent p-0.5 text-xs font-medium">
              {(["real", "test"] as Scope[]).map((s) => (
                <Link
                  key={s}
                  href={viewHref(view ?? "overview", s)}
                  className={`rounded-md px-2 py-1.5 text-center ${shown === s ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  {s === "real" ? "Real" : "Test"}
                </Link>
              ))}
            </div>
            <p className="mt-2 px-1 text-[0.6875rem] leading-snug text-muted-foreground">
              Test calls never count in the KPIs. Switch to review them.
            </p>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
