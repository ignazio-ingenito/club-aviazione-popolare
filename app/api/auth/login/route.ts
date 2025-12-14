import { cookies } from 'next/headers'

// app/api/auth/login/route.ts
export async function POST(req: Request) {
    const body = await req.json()

    const res = await fetch(`${process.env.DIRECTUS_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: body.email,
            password: body.password,
        }),
    })

    const { access_token, refresh_token } = await res.json()
    if (access_token && refresh_token) {
        cookies().set('access_token', access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
            path: '/',
            maxAge: 60 * 60 * 24 * 7 // 1 week
        })
        cookies().set('refresh_token', refresh_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
            path: '/',
            maxAge: 60 * 60 * 24 * 30 // 30 days
        })
    }
}
