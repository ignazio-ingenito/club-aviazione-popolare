import { NextResponse } from "next/server"
import { readItem } from "@directus/sdk"
import { directus } from "@/lib/directus"
import { Page } from "@/lib/types"

export async function GET(
    request: Request,
    context: { params: { key: string } }
) {
    const { key } = context.params

    const page = await directus.request(readItem("pages", key, {
        fields: ["*", "sections.*"],
        filter: { status: { _eq: "published" } },
        deep: { sections: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
    }))
    return NextResponse.json(page as Page)
}