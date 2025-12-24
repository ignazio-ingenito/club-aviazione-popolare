import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"

import styles from "./styles.module.css"

export default async function index() {
  const { content, content_title, description } = await getPage("costruire-un-aereo")

  return (
    <>
      <PageHero title={content_title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-7xl m-auto py-8 flex flex-col">
          <div
            className={`${styles.costruire_un_aereo} select-none text-muted-foreground`}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
