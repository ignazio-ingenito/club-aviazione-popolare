import { getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"
import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"
import Gallery from "@/components/gallery"
import { sanitizeHtml } from "@/lib/directus"

export default async function index() {
  const slug = "efficiency-race"
  const { icon } = await getSubMenuByUrl("/efficiency-race")
  const { author, date, title, description, content, cover, cover_offset_x, cover_offset_y } = await getFeedBySlug(slug)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <PageTitle title={title} icon={icon} />
          <div className="w-full flex justify-center">
            <Cover cover={cover} className={`cover h-auto w-full max-h-120 object-cover`} offset_x={cover_offset_x} offset_y={cover_offset_y} />
          </div>
          <Article
            title={title}
            cover={cover}
            author={author}
            date={date}
            content={content}
          />

          <div>
            <span
              className={`article select-none text-muted-foreground`}
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
            />
          </div>


          <Gallery slug={slug} exclude={cover?.id ? [cover?.id] : []} />
        </div>
      </div>
    </>
  )
}
