import { SiteFooter } from "@/components/site-footer"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"

import { NotebookText } from "lucide-react"
import { Header } from '@/components/header'


export default async function index() {
  const meta = await getMetadata()
  const menu = await getMenu()
  const page = await getPage("albo-storico")

  return (
    <div className="albo-storico flex min-h-screen flex-col">
      <Header
        title={meta.title}
        description={meta.description}
        menu={menu}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        instagramUrl={meta.instagram}
        twitterUrl={meta.twitter}

      />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative pt-24 pb-6 mb-6 bg-linear-to-br from-primary to-primary/80 text-secondary-foreground">
          <div className="container px-6">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">{page?.content_title}</h1>
            <div className="text-md leading-relaxed opacity-90">
              <TextToParagraphs text={page.description ?? ""} />
            </div>
          </div>
        </section>

        {/* Storia Section */}
        <section className="py-8 px-4 bg-background">
          <div className="w-full">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <NotebookText className="h-8 w-8" />
                <h2 className="text-3xl font-bold">{page?.content_title}</h2>
              </div>
              <div className=
                {
                  `select-none text-md text-muted-foreground ` +
                  `[&_table]:w-full [&_table]:border-collapse ` +
                  `[&_tr]:hover:text-accent ` +
                  `[&_th]:font-semibold [&_th]:text-accent [&_th,&_td]:text-center ` +
                  `[&_th:nth-child(3),&_th:nth-child(4),&_td:nth-child(3),&_td:nth-child(4)]:text-left ` +
                  `[&_td,&_th]:py-1.5 [&_tr]:border-y `
                } dangerouslySetInnerHTML={{ __html: sanitizeHtml(page.content ?? "") }}
              />
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div >
  )
}
