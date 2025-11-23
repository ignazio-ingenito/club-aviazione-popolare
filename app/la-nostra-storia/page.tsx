import ReactMarkdown from 'react-markdown'
import { findAll } from "domutils"
import { Element } from "domhandler"
import { parseDocument } from "htmlparser2"
import { render as domRender } from "dom-serializer"


import { Header } from '@/components/header'
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"
import { Users, Target, FileText, LucideIcon, LibraryBig } from "lucide-react"

const icons: LucideIcon[] = [Users, Target, FileText]

export function parseContent(html: string) {
  const doc = parseDocument(html)

  // Trova TUTTI gli <img> in ordine di apparizione
  const images = findAll(
    (el): el is Element => el instanceof Element && el.name === "img",
    doc.children
  )

  images.forEach((img, n) => {
    if (n == 0) {
      img.attribs.class += "pb-4 w-full"
      return
    }

    img.attribs.class = "px-4"
    img.attribs.class += n % 2 === 0 ? " pr-0 float-right" : " pl-0 float-left"
  })

  return domRender(doc)
}

export default async function index() {
  const meta = await getMetadata()
  const menu = await getMenu()
  const { content, content_title, description, sections } = await getPage("la-nostra-storia")

  return (
    <div className="la-nostra-storia flex min-h-screen flex-col">
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
          <div className="container px-6 ">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">{content_title}</h1>
            <div className="text-lg leading-relaxed opacity-90">
              <TextToParagraphs text={description ?? ""} />
            </div>
          </div>
        </section>

        {/* Storia Section */}
        <section className="py-8 px-4 bg-background">
          <div className="w-full">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <LibraryBig className="h-8 w-8" />
                <h2 className="text-3xl font-bold">{content_title}</h2>
              </div>
              <div className="space-y-4 text-lg leading-relaxed text-muted-foreground"
                dangerouslySetInnerHTML={{ __html: parseContent(sanitizeHtml(content ?? "")) }}
              />
            </div>
          </div>
        </section>

        <section>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div>
              <a href="">
                <img src="" alt="" />
              </a>
            </div>
            <div>
              <a href="">
                <img src="" alt="" />
              </a>
            </div>
          </div>
        </section>

        {/* Missione e Valori */}
        <section className="py-16 px-8 bg-muted/50">
          <div className="w-full">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{sections && sections[0].title}</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                {sections && sections[0].title}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {sections?.slice(1, 4).map(({ id, title, content }, i) => {
                const DynIcon = icons[i % icons.length]
                return (
                  <Card key={id} data-id={id}>
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center">
                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                          <DynIcon className="h-8 w-8 text-primary" />
                        </div>
                        <h3 className="text-xl font-bold mb-3">{title}</h3>
                        <p className="text-muted-foreground leading-relaxed">
                          {content}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div >
  )
}