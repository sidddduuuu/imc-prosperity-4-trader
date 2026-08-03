import { NextResponse } from "next/server";
import { getAuth0, isAuth0Configured } from "@/lib/auth0";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

/**
 * Bridge Auth0 session → Atlas API JWT.
 * Verifies the Auth0 ID token server-side against the FastAPI JWKS verifier.
 */
export async function GET() {
  if (!isAuth0Configured()) {
    return NextResponse.json(
      { configured: false, detail: "Auth0 env vars are not set" },
      { status: 503 }
    );
  }

  const session = await getAuth0().getSession();
  if (!session?.user) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  const idToken = session.tokenSet?.idToken;
  if (!idToken) {
    return NextResponse.json(
      { detail: "Auth0 session missing id_token" },
      { status: 401 }
    );
  }

  try {
    const res = await fetch(`${API_URL}/api/auth/auth0`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: idToken }),
      cache: "no-store",
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json({
      configured: true,
      authenticated: true,
      ...data,
      auth0_user: {
        sub: session.user.sub,
        email: session.user.email,
        name: session.user.name,
        picture: session.user.picture,
      },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Auth0 sync failed" },
      { status: 502 }
    );
  }
}
