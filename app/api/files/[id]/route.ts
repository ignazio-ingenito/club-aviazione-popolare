import { NextResponse } from 'next/server'

export async function GET(
    request: Request,
    { params }: { params: { id: string } }
) {
    const { id } = params
    console.log(`${process.env.DIRECTUS_URL}/assets/${id}`)
    const res = await fetch(`${process.env.DIRECTUS_URL}/assets/${id}`)
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
