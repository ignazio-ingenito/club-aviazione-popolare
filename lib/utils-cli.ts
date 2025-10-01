import DOMPurify from "isomorphic-dompurify"

// solo per componenti client
export function sanitizeHtmlClient(html: string) {
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
}
