import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"
import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

import styles from "./styles.module.css"

export default async function index() {
  const { content, content_title, description } = await getPage("cosa-facciamo")

  return (
    <>
      <PageHero title={content_title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-7xl mx-auto py-8 flex flex-col gap-y-8">
          <span
            className={`${styles.cosa_facciamo} select-none text-muted-foreground`}
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
