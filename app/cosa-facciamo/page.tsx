import { Cover } from "@/components/page/cover"
import { PageHero } from "@/components/page/hero"
import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

export default async function index() {
  const { content, title, description, cover, cover_offset_x, cover_offset_y } = await getPage("cosa-facciamo")


  return (
    <>
      <PageHero title={title} description={description} />

      <div className="article px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <Cover cover={cover} className={`w-full max-h-120 object-cover`} offset_x={cover_offset_x} offset_y={cover_offset_y} />
          <span
            className={`select-none text-muted-foreground`}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
