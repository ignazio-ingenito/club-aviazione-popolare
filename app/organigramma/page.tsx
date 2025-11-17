import { SiteFooter } from "@/components/site-footer"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"

import { Network } from "lucide-react"
import { Header } from '@/components/header'

import styles from "./styles.module.css"

export default async function index() {
  const meta = await getMetadata()
  const menu = await getMenu()
  const page = await getPage("organigramma")

  return (
    <div className="organigramma flex min-h-screen flex-col">
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

        {/* Page Section */}
        <section className="py-8 px-4 bg-background">
          <div className="flex items-center gap-3 mb-6">
            <Network className="h-8 w-8" />
            <h2 className="text-3xl font-bold">{page?.content_title}</h2>
          </div>
          <div className={styles.chart} dangerouslySetInnerHTML={{ __html: sanitizeHtml(page?.content ?? "") }} />
        </section>
      </main>
      <SiteFooter />
    </div >
  )
}
