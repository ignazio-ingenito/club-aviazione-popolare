import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value

    // Protected routes logic
    if (!token) {
        if (request.nextUrl.pathname.startsWith('/area-soci')) {
            return NextResponse.redirect(new URL('/login', request.url))
        }
    }

    // Redirect to dashboard if logged in and visiting login page
    if (token && request.nextUrl.pathname === '/login') {
        return NextResponse.redirect(new URL('/area-soci', request.url))
    }

    return NextResponse.next()
}

export const config = {
    matcher: [
        '/area-soci/:path*',
        '/login'
    ],
}
