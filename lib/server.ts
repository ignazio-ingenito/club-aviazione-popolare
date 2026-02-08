import {
  readItem,
  readItems,
  readMe,
  readSingleton,
  staticToken,
} from "@directus/sdk"

import { directus } from "./directus"

import {
  Category,
  Chapter,
  Feed,
  Meeting,
  MenuItem,
  Metadata,
  Page,
  SubMenuItem,
} from "./types"

const directusClient = () =>
  process.env.DIRECTUS_TOKEN
    ? directus.with(staticToken(process.env.DIRECTUS_TOKEN))
    : directus

export const formatDate = (date: Date) => {
  return new Date(date)
    .toLocaleDateString("it", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
    .replaceAll(/\s+/g, "-")
    .toLowerCase()
}

export const me = async (token: string) =>
  await directus.with(staticToken(token)).request(
    readMe({
      fields: ["*", "roles.*"],
    })
  )

export const getChapter = async (key: string): Promise<Chapter> => {
  const row = await directusClient().request(
    readItem("chapters", key, {
      filter: { status: { _eq: "published" } },
    })
  )
  return row as Chapter
}

export const getChapters = async (): Promise<Chapter[]> => {
  const rows = await directusClient().request(
    readItems("chapters", {
      filter: { status: { _eq: "published" } },
    })
  )
  return rows as Chapter[]
}

export const getCategory = async (id_category: string): Promise<Category> => {
  try {
    const res: unknown = (await directusClient().request(
      readItem("categories", id_category)
    )) as unknown
    const category = (res as unknown as { data?: unknown })?.data ?? res
    return (category ?? {}) as Category
  } catch (_err) {
    return ({
      id: id_category as unknown as number,
      title: "",
      description: "",
      status: "draft",
      sort: 0,
      feeds: [],
    } as unknown) as Category
  }
}

export const getFeed = async (id_feed: string): Promise<Feed> => {
  return await directusClient().request<Feed>(
    readItem("feeds", id_feed, {
      fields: ["*", "category.*"],
    })
  )
}

export const getFeedBySlug = async (slug: string): Promise<Feed> => {
  const rows = await directusClient().request<Feed[]>(
    readItems("feeds", {
      fields: ["*", "category.*"],
      filter: {
        status: { _eq: "published" },
        slug: { _eq: slug },
      },
    })
  )

  return rows[0] || ({} as Feed)
}

export const getFeeds = async (
  id: string,
  featured?: boolean,
  limit?: number
): Promise<Feed[]> => {
  const rows = await directusClient().request<Feed[]>(
    readItems("feeds", {
      fields: ["*", "category.id", "category.title", "category.description", "cover.*"],
      filter: {
        status: { _eq: "published" },
        category: { id },
        featured,
      },
      sort: ["-date"],
      limit,
    })
  )

  return rows.map(
    (e): Feed => ({
      ...e,
      date: e.date ? new Date(e.date) : new Date(),
    })
  )
}

export const getMetadata = async (): Promise<Metadata> => {
  const fallback: Metadata = {
    title: "",
    description: "",
    phone: "",
    email: "",
    address: "",
    facebook: "",
    twitter: "",
    instagram: "",
    map_type: "openstreetmap",
  }

  const normalizeMetadata = (raw: unknown): Metadata => {
    const data = (raw as { data?: unknown })?.data ?? raw
    const row = (Array.isArray(data) ? data[0] : data) as Partial<Metadata> | undefined
    return {
      ...fallback,
      ...(row ?? {}),
    }
  }

  try {
    const singletonRes: unknown = await directusClient().request(
      readSingleton("metadata")
    )
    const metadata = normalizeMetadata(singletonRes)

    const hasContent = [
      metadata.title,
      metadata.description,
      metadata.phone,
      metadata.email,
      metadata.address,
      metadata.facebook,
      metadata.twitter,
      metadata.instagram,
    ].some((value) => Boolean(value))

    if (hasContent) {
      return metadata
    }
  } catch (_err) {
    // Fallback below handles non-singleton metadata setups.
  }

  try {
    const itemsRes: unknown = await directusClient().request(
      readItems("metadata", {
        limit: 1,
      })
    )
    return normalizeMetadata(itemsRes)
  } catch (_err) {
    return fallback
  }
}

export const getMeetings = async (): Promise<Meeting[]> => {
  return (await directusClient().request(
    readItems("meetings", {
      filter: { status: { _eq: "published" } }
    }))
  ) as Meeting[]
}

export const getMenu = async (): Promise<MenuItem[]> => {
  const res: unknown = (await directusClient().request(
    readItems("site_menu", {
      fields: ["*", "submenu.*"],
      sort: ["sort"],
      filter: { status: { _eq: "published" } },
      deep: {
        submenu: { _filter: { status: { _eq: "published" } }, sort: ["sort"] },
      },
    })
  )) as unknown

  const menu = (res as unknown as { data?: unknown })?.data ?? res
  return Array.isArray(menu) ? (menu as MenuItem[]) : []
}

export const getSubMenuByUrl = async (url: string): Promise<SubMenuItem> => {
  try {
    const res: unknown = (await directusClient().request(
      readItems("site_submenu", {
        filter: { url: { _eq: url } },
      })
    )) as unknown
    const rows = (res as unknown as { data?: unknown })?.data ?? res
    return (Array.isArray(rows) ? rows[0] : {}) as SubMenuItem
  } catch (_err) {
    return {} as SubMenuItem
  }
}

export const getPage = async (key: string): Promise<Page> => {
  // return await directus.request(readItem("pages", key)) as Page
  try {
    const res: unknown = (await directusClient().request(
      readItem("pages", key, {
        fields: ["*", "cover.*", "sections.*"],
        filter: { status: { _eq: "published" } },
        deep: {
          sections: { filter: { status: { _eq: "published" } }, sort: ["sort"] },
        },
      })
    )) as unknown
    const page = (res as unknown as { data?: unknown })?.data ?? res
    return (page ?? {}) as Page
  } catch (_err) {
    return {} as Page
  }
}
