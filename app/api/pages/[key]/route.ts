import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { readItem } from "@directus/sdk"
import { directus } from "@/lib/directus"
import { Page } from "@/lib/types"

export const dynamic = "force-dynamic"

export async function GET(
    _request: NextRequest,
    context: { params: Promise<{ key: string }> }
) {
    const { key } = await context.params

    const page = await directus.request(readItem("pages", key, {
        fields: ["*", "cover.*", "sections.*"],
        filter: { status: { _eq: "published" } },
        deep: { sections: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
    }))
    return NextResponse.json(page as Page)
}
