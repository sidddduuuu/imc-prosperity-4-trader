import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { getAuth0, isAuth0Configured } from "./lib/auth0";

/**
 * Next.js 16 proxy boundary for Auth0 auth routes + rolling sessions.
 */
export async function proxy(request: NextRequest) {
  if (!isAuth0Configured()) {
    return NextResponse.next();
  }
  return getAuth0().middleware(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
