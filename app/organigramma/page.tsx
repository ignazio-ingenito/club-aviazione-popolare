import { PageHero } from "@/components/page/hero"
import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

export default async function index() {
  const { content, title, description } = await getPage("organigramma")

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8">
          <div
            className="select-none bg-background text-muted-foreground mb-12"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
