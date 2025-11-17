import { NextResponse } from "next/server"
import { readItems } from "@directus/sdk"
import { directus } from "@/lib/server"
import { MenuItem } from "@/lib/types"

export async function GET() {
    const menu = await directus.request(readItems("site_menu", {
        fields: ["*", "submenu.*"],
        filter: { status: { _eq: "published" } },
        sort: ["sort"],
        deep: { submenu: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
    }))
    return NextResponse.json(menu as MenuItem[])
}