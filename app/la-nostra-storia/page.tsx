import { PageCover } from "@/components/page/cover"
import { PageHero } from "@/components/page/hero"
import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"
import { Convergence } from "next/font/google"

export default async function index() {
  const { title, description, content, cover } = await getPage("la-nostra-storia")

  return (
    <>
      <PageHero title={title} description={description} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <PageCover cover={cover} className="max-h-120 w-full" />
          <span
            className="article text-muted-foreground select-none"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content) }}
          />
        </div>
      </div>
    </>
  )
}