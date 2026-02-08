
import { getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import { Cover } from "@/components/page/cover"
import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"
import { sanitizeHtml } from "@/lib/directus"

interface Props {
  params: Promise<{
    slug: string
  }>
}

export default async function index({ params }: Props) {
  const { slug } = await params
  const { icon } = await getSubMenuByUrl(`/trofei/${slug}`)
  const { title, content, description, cover, cover_offset_x, cover_offset_y } = await getFeedBySlug(slug)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl mx-auto py-8 flex flex-col gap-y-8">
          <div>
            <PageTitle title={title} icon={icon} />
          </div>
          <div className="w-full flex justify-center">
            <Cover cover={cover} className="w-full max-h-120 object-cover" offset_x={cover_offset_x} offset_y={cover_offset_y} />
          </div>
          <span
            className={`article select-none text-sm text-muted-foreground [&_td]:border-b [&_td]:border-neutral-300 [&_td]:p-2 [&_th]:border-y [&_th]:border-neutral-300 [&_th]:p-2`}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
