import { createDirectus, rest } from "@directus/sdk"
import { JSDOM } from "jsdom"
import createDOMPurify, { WindowLike } from "dompurify"
import { Cover } from "./types"

export const DEFAULT_COVER: Cover = {
  id: "4f92d286-a525-4f7d-90ba-1dfbf719e04e",
  title: "Cover",
  type: "image",
  width: 1536,
  height: 1024,
  focal_point_x: 732,
  focal_point_y: 472,
}

const window = new JSDOM("").window as unknown as WindowLike
const DOMPurify = createDOMPurify(window)

DOMPurify.addHook("afterSanitizeAttributes", (currentNode) => {
  if (
    currentNode.tagName === "A" &&
    currentNode.getAttribute("target") === "_blank"
  ) {
    currentNode.setAttribute("rel", "noopener noreferrer")
  }
})

export const fetchOptions =
  process.env.NODE_ENV === "development"
    ? { cache: "no-store" }
    : { next: { revalidate: 60 } }

export const directus = createDirectus(
  process.env.DIRECTUS_URL ?? "http://localhost:8055"
).with(
  rest({
    onRequest: (options) => ({ ...options, ...fetchOptions } as RequestInit),
  })
)

export const getImageUrl = ({ id, width, height }: Cover = DEFAULT_COVER): string => {
  const url = new URL(`assets/${id}`, process.env.DIRECTUS_URL)
  if (width) url.searchParams.set("width", width.toString())
  if (height) url.searchParams.set("height", height.toString())
  return url.toString()
}

export const sanitizeHtml = (html: string = "") =>
  DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
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
    ALLOWED_ATTR: [
      "href",
      "target",
      "rel",
      "class",
      "src",
      "alt",
      "title",
      "width",
      "height",
      "loading",
      "decoding",
      "colspan",
      "style",
    ],
  })
