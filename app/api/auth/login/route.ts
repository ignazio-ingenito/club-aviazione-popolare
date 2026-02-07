import { cookies } from 'next/headers'

// app/api/auth/login/route.ts
export async function POST(req: Request) {
    const body = await req.json()

    const directusInternalUrl =
        process.env.DIRECTUS_INTERNAL_URL ?? process.env.DIRECTUS_URL

    if (!directusInternalUrl) {
        return Response.json({ ok: false, error: "DIRECTUS_INTERNAL_URL not set" }, { status: 500 })
    }

    const res = await fetch(`${directusInternalUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: body.email,
            password: body.password,
        }),
    })

    const payload = await res.json().catch(() => ({}))

    if (!res.ok) {
        return Response.json(
            { ok: false, error: payload?.errors ?? payload ?? "Login failed" },
            { status: res.status }
        )
    }

    const { access_token, refresh_token } = payload as {
        access_token?: string
        refresh_token?: string
    }

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

    return Response.json({ ok: true })
}
