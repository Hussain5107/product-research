"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Search,
  Sparkles,
  Lightbulb,
  Sun,
  PanelLeftClose,
  PanelLeft,
  Moon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const NAV_ITEMS = [
  { href: "/category-research", label: "UAE Category Agent", icon: Search },
];

type Theme = "light" | "dark" | "system";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<Theme>("dark");

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-950">
      <aside
        className={cn(
          "flex flex-col border-r border-slate-200 bg-white transition-all duration-200",
          sidebarOpen ? "w-[240px] shrink-0" : "w-0"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
          {sidebarOpen ? (
            <div className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600">
                <Lightbulb className="h-5 w-5" />
              </span>
              <span>
                <span className="block font-semibold tracking-tight text-slate-950">ProductHunter Agent</span>
                <span className="block text-xs text-slate-500">Step 1: Category research</span>
              </span>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              className="h-9 w-9"
            >
              <PanelLeft className="h-4 w-4" />
              <span className="sr-only">Open sidebar</span>
            </Button>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            const show = sidebarOpen;

            return (
              <Tooltip key={item.href} delayDuration={0}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
                      !show && "sr-only"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                </TooltipTrigger>
                {!show && (
                  <TooltipContent side="right">
                    <span>{item.label}</span>
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </nav>

        <div className="border-t p-3 space-y-3">
          {sidebarOpen && (
            <div className="rounded-xl bg-slate-100 p-3">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                <Sparkles className="h-4 w-4 text-indigo-600" />
                Focus Mode
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Other modules are hidden while we build the first UAE category research agent.
              </p>
            </div>
          )}
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <Badge variant="secondary" className="font-mono text-xs">
                v0.1.0
              </Badge>
            )}
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="h-8 w-8"
                title="Toggle theme"
              >
                {theme === "dark" ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
                <span className="sr-only">Toggle theme</span>
              </Button>
              {sidebarOpen && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarOpen(false)}
                  className="h-8 w-8"
                  title="Collapse sidebar"
                >
                  <PanelLeftClose className="h-4 w-4" />
                  <span className="sr-only">Collapse sidebar</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
