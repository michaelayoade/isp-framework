import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define public paths that don't require authentication
const publicPaths = [
  '/',
  '/login',
  '/admin/login',
  '/customer/login',
  '/reseller/login',
  '/unauthorized',
  '/api',
  '/_next',
  '/favicon.ico',
  '/static',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Skip middleware for public paths
  if (publicPaths.some(path => pathname === path || pathname.startsWith(path + '/')) || publicPaths.includes(pathname)) {
    return NextResponse.next();
  }
  
  // Get tokens and role from cookies
  const accessToken = request.cookies.get('access_token')?.value;
  const userRole = request.cookies.get('user_role')?.value;
  
  // Redirect to login if no token and accessing protected route
  if (!accessToken) {
    // If accessing a role-specific area, redirect to that role's login
    if (pathname.startsWith('/admin')) {
      return NextResponse.redirect(new URL('/admin/login', request.url));
    } else if (pathname.startsWith('/customer')) {
      return NextResponse.redirect(new URL('/customer/login', request.url));
    } else if (pathname.startsWith('/reseller')) {
      return NextResponse.redirect(new URL('/reseller/login', request.url));
    }
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Check if user is accessing a role-specific path
  if (pathname.startsWith('/admin') && userRole !== 'admin') {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }
  
  if (pathname.startsWith('/customer') && userRole !== 'customer') {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }
  
  if (pathname.startsWith('/reseller') && userRole !== 'reseller') {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }
  
  return NextResponse.next();
}

// Configure which paths the middleware should run on
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
