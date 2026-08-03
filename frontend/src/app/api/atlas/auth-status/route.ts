import { NextResponse } from "next/server";
import { isAuth0Configured } from "@/lib/auth0";

export async function GET() {
  return NextResponse.json({
    configured: isAuth0Configured(),
    loginUrl: "/auth/login",
    logoutUrl: "/auth/logout",
    signupUrl: "/auth/login?screen_hint=signup",
  });
}
