import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACTIVE_AGENT_PATH = "/category-research";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/" || pathname === ACTIVE_AGENT_PATH || pathname.startsWith(`${ACTIVE_AGENT_PATH}/`)) {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = ACTIVE_AGENT_PATH;
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!api|_next|favicon.ico|.*\\..*).*)"],
};
