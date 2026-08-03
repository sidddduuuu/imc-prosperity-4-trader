import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { getAuth0, isAuth0Configured } from "./lib/auth0";

/** Public routes — everything else requires Auth0 (or local /login fallback). */
function isPublicPath(pathname: string): boolean {
  if (pathname === "/") return true;
  if (pathname.startsWith("/auth")) return true;
  if (pathname === "/login") return true;
  if (pathname === "/api/atlas/auth-status") return true;
  if (pathname === "/api/health") return true;
  // static / next internals already excluded by matcher
  return false;
}

/**
 * Auth0 session gate: landing page is public; all product features require login.
 */
export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Auth0 not configured → only allow local login fallback for features
  if (!isAuth0Configured()) {
    if (isPublicPath(pathname)) {
      return NextResponse.next();
    }
    const login = new URL("/login", request.nextUrl.origin);
    login.searchParams.set("returnTo", `${pathname}${search}`);
    return NextResponse.redirect(login);
  }

  const auth0 = getAuth0();
  const authRes = await auth0.middleware(request);

  // Always let Auth0 handlers finish (/auth/login, callback, logout, …)
  if (pathname.startsWith("/auth")) {
    return authRes;
  }

  if (isPublicPath(pathname)) {
    return authRes;
  }

  const session = await auth0.getSession(request);
  if (!session?.user) {
    const login = new URL("/auth/login", request.nextUrl.origin);
    login.searchParams.set("returnTo", `${pathname}${search || ""}`);
    // Preserve Auth0 middleware cookies (rolling sessions) on the redirect
    const redirect = NextResponse.redirect(login);
    authRes.cookies.getAll().forEach((cookie) => {
      redirect.cookies.set(cookie.name, cookie.value);
    });
    return redirect;
  }

  return authRes;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
