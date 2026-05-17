"use client";

import * as TabsPrimitive from "@radix-ui/react-tabs";

import { cn } from "@/lib/utils/cn";

const Tabs = TabsPrimitive.Root;

const TabsList = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) => (
  <TabsPrimitive.List
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-lg bg-[var(--st-muted)]/60 p-1 text-[var(--st-fg-muted)] ring-1 ring-[var(--st-border)]",
      className,
    )}
    {...props}
  />
);

const TabsTrigger = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) => (
  <TabsPrimitive.Trigger
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--st-accent-ring)] disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[var(--st-surface)] data-[state=active]:text-[var(--st-fg)] data-[state=active]:shadow-sm",
      className,
    )}
    {...props}
  />
);

const TabsContent = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) => (
  <TabsPrimitive.Content
    className={cn("mt-4 focus-visible:outline-none", className)}
    {...props}
  />
);

export { Tabs, TabsList, TabsTrigger, TabsContent };
