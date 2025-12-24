import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

interface Props {
  params: {
    key: string
  }
}

export default async function index({ params }: Props) {
  const { content, content_title, description, title } = await getPage(
    params.key
  )
  return (
    <>
      <PageHero description={description} title={content_title} />

      <div className="py-8 flex flex-col gap-y-8 max-w-7xl m-auto">
        <PageTitle title={content_title} icon="map-pin-house" />

        <div
          className="text-muted-foreground text-md [&_img]:mr-4 [&_img]:pt-2 [&_img]:min-[600px]:float-left [&_img]:max-[600px]:mb-6 [&_h2]:text-2xl [&_h2]:not-first-of-type:pt-6 [&_h2]:pb-2"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
        />
      </div>
    </>
  )
}
