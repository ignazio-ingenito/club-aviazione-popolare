declare module "sanitize-html" {
  interface Defaults {
    allowedTags: string[]
    allowedAttributes: Record<string, string[]>
  }

  interface SanitizeHtml {
    (html: string, options?: unknown): string
    defaults: Defaults
  }

  const sanitize: SanitizeHtml
  export = sanitize
}
