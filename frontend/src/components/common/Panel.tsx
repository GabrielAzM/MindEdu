import { PropsWithChildren } from "react";

import { cn } from "../../lib/utils";

export function Panel({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <section className={cn("rounded-xl border border-sky-100 bg-white p-4 shadow-sm", className)}>{children}</section>;
}
