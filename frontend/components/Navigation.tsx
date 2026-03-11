"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/calculator", label: "Calculator" },
  { href: "/sweet-spots", label: "Sweet Spots" },
  { href: "/graph", label: "Graph Explorer" },
  { href: "/quiz", label: "Strategy Quiz" },
  { href: "/billing", label: "Billing" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-rose-100 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-bold text-rose-600">
          RedeemFlow
        </Link>
        <div className="flex items-center gap-6">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "text-rose-600"
                  : "text-gray-500 hover:text-rose-500"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
