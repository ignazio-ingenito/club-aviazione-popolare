import { NextResponse } from 'next/server'
import type { NextRequest } from "next/server"

export async function GET(
    _request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    const { id } = await context.params
    const directusInternalUrl =
        process.env.DIRECTUS_INTERNAL_URL ?? process.env.DIRECTUS_URL

    if (!directusInternalUrl) {
        return NextResponse.json({ error: 'DIRECTUS_INTERNAL_URL not set' }, { status: 500 })
    }

    const res = await fetch(`${directusInternalUrl}/assets/${id}`)
    // const res = await fetch(`${process.env.DIRECTUS_URL}/assets/${id}`, {
    //     headers: {
    //         Authorization: `Bearer ${process.env.DIRECTUS_PRIVATE_TOKEN}`,
    //     },
    // })

    if (!res.ok) {
        return NextResponse.json({ error: 'File non trovato' }, { status: res.status })
    }

    const contentType = res.headers.get('content-type') || 'application/octet-stream'
    const buffer = await res.arrayBuffer()

    return new NextResponse(buffer, {
        headers: { 'Content-Type': contentType },
    })
}
