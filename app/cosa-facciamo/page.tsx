import { SiteFooter } from "@/components/site-footer"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"

import { TrafficCone } from "lucide-react"
import { Header } from '@/components/header'


export default async function index() {
  const menu = await getMenu()
  const meta = await getMetadata()
  const page = await getPage("cosa-facciamo")

  return (
    <div className="cosa-facciamo flex min-h-screen flex-col">
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
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Cosa facciamo</h1>
            <div className="text-md leading-relaxed opacity-90">
              <TextToParagraphs text={page.description ?? ""} />
            </div>
          </div>
        </section>

        {/* Page Section */}
        <section className="py-8 px-4 bg-background">
          <div className="container">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <TrafficCone className="h-8 w-8" />
                <h2 className="text-3xl font-bold">{page?.content_title}</h2>
              </div>
              <div className={
                `select-none text-md text-muted-foreground ` +
                `[&_a]:text-accent [&_a]:hover:underline [&_p]:py-2 ` +
                `[&_ul]:list-disc [&_ul]:pl-8 [&_ul]:pb-4 [&_li]:py-1 ` +
                `[&_h1]:text-3xl [&_h1]:mt-6 [&_h1]:mb-2 ` +
                `[&_h2]:text-2xl [&_h2]:mt-4 [&_h2]:mb-1 ` +
                `[&_img]:float-right [&_img]:bg-transparent `
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
