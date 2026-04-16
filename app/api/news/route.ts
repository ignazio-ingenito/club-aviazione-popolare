import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

import { toNewsListItem } from "@/lib/news-list"
import { getFeeds } from "@/lib/server"
import type { Feed } from "@/lib/types"

export const dynamic = "force-dynamic"

const DEFAULT_LIMIT = 9
const MAX_LIMIT = 24

const intParam = (value: string | null, fallback: number) => {
  const parsed = Number.parseInt(value || "", 10)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback
}

const idListParam = (value: string | null) =>
  new Set(
    (value || "")
      .split(",")
      .map((id) => Number.parseInt(id, 10))
      .filter((id) => Number.isFinite(id))
  )

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const offset = intParam(searchParams.get("offset"), 0)
  const limit = Math.min(intParam(searchParams.get("limit"), DEFAULT_LIMIT), MAX_LIMIT)
  const exclude = idListParam(searchParams.get("exclude"))
  const rows = (await getFeeds("news")) as Feed[]
  const filteredRows = rows.filter((row) => !exclude.has(row.id))
  const items = filteredRows.slice(offset, offset + limit).map(toNewsListItem)

  return NextResponse.json({
    items,
    hasMore: filteredRows.length > offset + limit,
  })
}
