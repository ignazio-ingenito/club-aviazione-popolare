import { createDirectus, rest } from "@directus/sdk"
import sanitizeHtmlLib from "sanitize-html"
import { Cover } from "./types"

const DIRECTUS_INTERNAL_URL =
  process.env.DIRECTUS_INTERNAL_URL ??
  process.env.DIRECTUS_URL ??
  "http://localhost:8055"

const DIRECTUS_PUBLIC_URL =
  process.env.DIRECTUS_PUBLIC_URL ??
  process.env.DIRECTUS_URL ??
  "http://localhost:8055"

const admin_uuid = "4f5a3ebf-d050-4884-a55a-b09af71c8036"
export const DEFAULT_COVER: Cover = {
  id: "4f92d286-a525-4f7d-90ba-1dfbf719e04e",
  title: "Cover",
  width: 1536,
  height: 1024,
  focal_point_x: 732,
  focal_point_y: 472,
  user_created: admin_uuid,
  date_created: new Date(),
  user_updated: admin_uuid,
  date_updated: new Date(),
}

export const fetchOptions =
  process.env.NODE_ENV === "development"
    ? { cache: "no-store" }
    : { next: { revalidate: 60 } }

export const directus = createDirectus(
  DIRECTUS_INTERNAL_URL
).with(
  rest({
    onRequest: (options) => ({ ...options, ...fetchOptions } as RequestInit),
  })
)

export const getImageUrl = (
  cover?: Partial<Cover> | string | null,
  widthOverride?: number,
  heightOverride?: number
): string => {
  const coverObj = typeof cover === "string" ? { id: cover } : cover
  const id = coverObj?.id ?? DEFAULT_COVER.id
  const url = new URL(`assets/${id}`, DIRECTUS_PUBLIC_URL)
  const urlWidth =
    widthOverride ??
    (typeof cover === "string" ? undefined : cover?.width) ??
    DEFAULT_COVER.width
  const urlHeight =
    heightOverride ??
    (typeof cover === "string" ? undefined : cover?.height) ??
    DEFAULT_COVER.height
  if (urlWidth) url.searchParams.set("width", urlWidth.toString())
  if (urlHeight) url.searchParams.set("height", urlHeight.toString())
  return url.toString()
}

export const sanitizeHtml = (html: string = "") =>
  sanitizeHtmlLib(html, {
    allowedTags: [
      "a",
      "img",
      "br",
      "p",
      "b",
      "i",
      "strong",
      "em",
      "ul",
      "ol",
      "li",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "blockquote",
      "code",
      "pre",
      "div",
      "span",
      "table",
      "thead",
      "tbody",
      "tr",
      "td",
      "th",
      "hr",
    ],
    allowedAttributes: {
      a: ["href", "target", "rel", "class", "title"],
      img: [
        "src",
        "alt",
        "title",
        "width",
        "height",
        "loading",
        "decoding",
        "class",
        "style",
      ],
      td: ["colspan", "class", "style"],
      th: ["colspan", "class", "style"],
      "*": ["class", "style"],
    },
    transformTags: {
      a: (tagName: string, attribs: Record<string, string>) => {
        if (attribs.target === "_blank") {
          attribs.rel = "noopener noreferrer"
        }
        return { tagName, attribs }
      },
    },
  })
