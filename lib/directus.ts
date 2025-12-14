import { createDirectus, rest } from "@directus/sdk"
import { JSDOM } from "jsdom"
import createDOMPurify, { WindowLike } from "dompurify"

export const DEFAULT_COVER = "8f79eaaf-1e06-459c-8c81-18f02c8c72f3"

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

export const getImageUrl = (
  id: string = DEFAULT_COVER,
  width?: number,
  height?: number
): string => {
  const url = new URL(`assets/${id}`, process.env.DIRECTUS_URL)
  if (width) url.searchParams.set("width", width?.toString())
  if (height) url.searchParams.set("height", height?.toString())
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
