"use server"

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

export const getChapters = async (): Promise<Chapter[]> => {
  const rows = await directus.request(
    readItems("chapters", {
      filter: { status: { _eq: "published" } },
    })
  )
  return rows as Chapter[]
}

export const getCategory = async (id_category: string): Promise<Category> => {
  const category = await directus.request(readItem("categories", id_category))
  return category as Category
}

export const getFeed = async (id_feed: string): Promise<Feed> => {
  return await directus.request<Feed>(
    readItem("feeds", id_feed, {
      fields: ["*", "category.*"],
    })
  )
}

export const getFeedBySlug = async (slug: string): Promise<Feed> => {
  const rows = await directus.request<Feed[]>(
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
  const rows = await directus.request<Feed[]>(
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
  return (await directus.request(readSingleton("metadata"))) as Metadata
}

export const getMeetings = async (): Promise<Meeting[]> => {
  return (await directus.request(readItems("meetings"))) as Meeting[]
}

export const getMenu = async (): Promise<MenuItem[]> => {
  const menu = await directus.request(
    readItems("site_menu", {
      fields: ["*", "submenu.*"],
      sort: ["sort"],
      filter: { status: { _eq: "published" } },
      deep: {
        submenu: { _filter: { status: { _eq: "published" } }, sort: ["sort"] },
      },
    })
  )
  return menu as MenuItem[]
}

export const getSubMenuByUrl = async (url: string): Promise<SubMenuItem> => {
  const subMenu = await directus.request(
    readItems("site_submenu", {
      filter: { url: { _eq: url } },
    })
  )
  return subMenu[0] as SubMenuItem
}

export const getPage = async (key: string): Promise<Page> => {
  // return await directus.request(readItem("pages", key)) as Page
  const page = await directus.request(
    readItem("pages", key, {
      fields: ["*", "sections.*"],
      filter: { status: { _eq: "published" } },
      deep: {
        sections: { filter: { status: { _eq: "published" } }, sort: ["sort"] },
      },
    })
  )
  return page as Page
}
