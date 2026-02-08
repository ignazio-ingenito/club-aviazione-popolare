import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"


export default async function index() {
  const { content, title, description, cover } = await getPage("costruire-un-aereo")

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col">
          <Cover cover={cover} className="w-full max-h-120 object-[50%_92%]" />
          <span
            className={`article select-none text-muted-foreground`}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
