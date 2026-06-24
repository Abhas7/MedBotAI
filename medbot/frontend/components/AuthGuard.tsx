"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const authed = isAuthenticated();
      
      const isAuthRoute = pathname === "/login" || pathname === "/register";
      const isProtectedRoute = pathname.startsWith("/chat");

      if (isProtectedRoute && !authed) {
        router.replace("/login");
      } else if (isAuthRoute && authed) {
        router.replace("/chat");
      } else {
        setLoading(false);
      }
    };

    checkAuth();
    
    // Listen for storage events (to synchronize tabs)
    const handleStorageChange = () => {
      checkAuth();
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [pathname, router]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-emerald-400">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20 animate-ping"></div>
          <div className="absolute inset-0 rounded-full border-4 border-t-emerald-400 border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
        </div>
        <p className="mt-4 text-sm font-medium tracking-wide animate-pulse">
          Securing Medical Workspace...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
