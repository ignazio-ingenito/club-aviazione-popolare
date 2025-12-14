import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

import styles from "./styles.module.css"

export default async function index() {
  const { content, content_title, description } = await getPage("costruire-un-aereo")

  return (
    <>
      <PageHero title={content_title} description={description} />

      <div className="py-8 flex flex-col gap-y-8 max-w-5xl m-auto">
        <PageTitle title={content_title} description={description} icon="traffic-cone" />

        <div
          className={`${styles.costruire_un_aereo} select-none text-muted-foreground`}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
        />
      </div>
    </>
  )
}
