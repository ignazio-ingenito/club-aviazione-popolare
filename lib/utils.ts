import sanitize from "sanitize-html"
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { unstable_noStore as noStore } from "next/cache"
import { createDirectus, readItem, readItems, readSingleton, rest } from "@directus/sdk"
import { UUID } from "crypto"

export type Metadata = {
  title: string
  description?: string
  phone?: string
  email?: string
  address?: string
  facebook?: string
  twitter?: string
  instagram?: string
}

export type Page = {
  id: number
  key: string
  title: string
  content_title?: string
  content?: string
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
  description?: string
}

export type Section = {
  id: number
  key: string
  title: string
  status: string
  content?: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
  description?: string
}

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))
export const directus = createDirectus(process.env.DIRECTUS_URL ?? "http://localhost:8055").with(rest())

export const getMetadata = async (): Promise<Metadata> => {
  noStore() // prevent caching
  return await directus.request(readSingleton("metadata")) as Metadata
}

export const getMenuSections = async (): Promise<Section[]> => {
  // http://localhost:8055/items/site_menu

  noStore() // prevent caching
  const sections = await directus.request(readItems("menu_sections", {
    filter: { status: { _eq: "published" } },
    sort: ["sort"]
  }))
  return sections as Section[]
}

export const getPage = async (key: string): Promise<Page> => {
  noStore() // prevent caching
  return await directus.request(readItem("pages", key)) as Page
}

export const getPageSections = async (key: string): Promise<Section[]> => {
  noStore() // prevent caching
  const sections = await directus.request(readItems("page_sections", {
    filter: { key: { _eq: key }, status: { _eq: "published" } },
    sort: ["sort"]
  }))
  return sections as Section[]
}

// solo per componenti server
export const sanitizeHtml = (html: string) => {
  return sanitize(html, {
    allowedTags: sanitize.defaults.allowedTags.concat(["img"]),
    allowedAttributes: {
      ...sanitize.defaults.allowedAttributes,
      img: ["src", "alt", "title", "width", "height", "loading", "decoding"],
      a: ["href", "name", "target", "rel"],
    },
    // se vuoi forzare rel noopener su link esterni:
    transformTags: {
      a: (tagName: string, attribs: any) => ({
        tagName: "a",
        attribs: {
          ...attribs,
          rel: attribs.target === "_blank" ? "noopener noreferrer" : attribs.rel,
        },
      }),
    },
  })
}