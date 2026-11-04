"use client";

import Link from "next/link";
import {
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
      </SidebarContent>
    </Sidebar>
  );
}
