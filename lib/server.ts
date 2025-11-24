import sanitize from "sanitize-html"
import { unstable_noStore as noStore } from "next/cache"
import { createDirectus, readItem, readItems, readSingleton, rest } from "@directus/sdk"

import { Category, Chapter, Feed, Meeting, MenuItem, Metadata, Page } from "./types"


export const directus = createDirectus(process.env.DIRECTUS_URL ?? "http://localhost:8055").with(rest())

export const getChapters = async (): Promise<Chapter[]> => {
  noStore() // prevent caching
  const rows = await directus.request(readItems("chapters", {
    filter: { status: { _eq: "published" } },
  }))
  return rows as Chapter[]
}

export const getCategory = async (id: string): Promise<Category> => {
  noStore() // prevent caching
  const category = await directus.request(readItem("categories", id))
  return category as Category
}

export const getFeed = async (id: string): Promise<Feed> => {
  noStore() // prevent caching
  return await directus.request<Feed>(readItem("feeds", id, {
    fields: ["*", "category.id", "category.title", "category.description"],
    filter: {
      status: { _eq: "published" }
    }
  }))
}

export const getFeeds = async (id: string): Promise<Feed[]> => {
  noStore() // prevent caching
  const rows = await directus.request<Feed[]>(readItems("feeds", {
    fields: ["*", "category.id", "category.description"],
    filter: {
      status: { _eq: "published" },
      category: { id },
    },
    sort: ["-date"],
  }))

  return rows.map((e): Feed => ({
    ...e,
    date: new Date(e.date)
  }))
}

export const getMetadata = async (): Promise<Metadata> => {
  noStore() // prevent caching
  return await directus.request(readSingleton("metadata")) as Metadata
}

export const getMeetings = async (): Promise<Meeting[]> => {
  noStore() // prevent caching
  return await directus.request(readItems("meetings")) as Meeting[]
}

export const getMenu = async (): Promise<MenuItem[]> => {
  noStore() // prevent caching
  const menu = await directus.request(readItems("site_menu", {
    fields: ["*", "submenu.*"],
    sort: ["sort"],
    filter: { status: { _eq: "published" } },
    deep: { submenu: { _filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
  }))
  return menu as MenuItem[]
}

export const getPage = async (key: string): Promise<Page> => {
  noStore() // prevent caching
  // return await directus.request(readItem("pages", key)) as Page
  const page = await directus.request(readItem("pages", key, {
    fields: ["*", "sections.*"],
    filter: { status: { _eq: "published" } },
    deep: { sections: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
  }))
  return page as Page
}

export const sanitizeHtml = (html: string) => {
  return sanitize(html, {
    allowedTags: sanitize.defaults.allowedTags.concat(["img"]),
    allowedAttributes: {
      ...sanitize.defaults.allowedAttributes,
      img: ["src", "alt", "title", "width", "height", "loading", "decoding"],
      a: ["href", "name", "target", "rel"],
    },
    transformTags: {
      a: (attribs: any) => ({
        tagName: "a",
        attribs: {
          ...attribs,
          rel: attribs.target === "_blank" ? "noopener noreferrer" : attribs.rel,
        },
      }),
    },
  })
}