import { getChapter } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageTitle } from "@/components/page/title"

interface Props {
  params: {
    slug: string
  }
}

export default async function index({ params }: Props) {
  const { slug } = params
  const { description, name } = await getChapter(slug)
  return (
    <>
      <div className="py-8 flex flex-col gap-y-8 max-w-5xl m-auto">
        <PageTitle title={name} icon="map-pin-house" />

        <div
          className="text-muted-foreground text-md [&_img]:mr-4 [&_img]:pt-2 [&_img]:min-[600px]:float-left [&_img]:max-[600px]:mb-6 [&_h2]:text-2xl [&_h2]:not-first-of-type:pt-6 [&_h2]:pb-2"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(description ?? "") }}
        />
      </div>
    </>
  )
}
