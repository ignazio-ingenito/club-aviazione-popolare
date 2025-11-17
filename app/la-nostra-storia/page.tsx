import ReactMarkdown from 'react-markdown'
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"

import { Users, Target, FileText, LucideIcon, LibraryBig } from "lucide-react"
import { Header } from '@/components/header'

const icons: LucideIcon[] = [Users, Target, FileText]

export default async function index() {
  const meta = await getMetadata()
  const menu = await getMenu()
  const page = await getPage("la-nostra-storia")

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
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">{page?.content_title}</h1>
            <div className="text-lg leading-relaxed opacity-90">
              <TextToParagraphs text={page.description ?? ""} />
            </div>
          </div>
        </section>

        {/* Storia Section */}
        <section className="py-8 px-4 bg-background">
          <div className="w-full">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <LibraryBig className="h-8 w-8" />
                <h2 className="text-3xl font-bold">{page?.content_title}</h2>
              </div>
              <div className="space-y-4 text-lg leading-relaxed text-muted-foreground [&_img]:w-full [&_img]:object-cover"
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(page.content ?? "") }}
              />
            </div>
          </div>
        </section>

        {/* Missione e Valori */}
        <section className="py-16 px-8 bg-muted/50">
          <div className="w-full">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{page?.sections && page.sections[0].title}</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                {page?.sections && page.sections[0].title}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {page?.sections?.slice(1, 4).map((sec, i) => {
                const DynIcon = icons[i % icons.length]
                return (
                  <Card key={sec.id} data-id={sec.id}>
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center">
                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                          <DynIcon className="h-8 w-8 text-primary" />
                        </div>
                        <h3 className="text-xl font-bold mb-3">{sec.title}</h3>
                        <p className="text-muted-foreground leading-relaxed">
                          {sec.content}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        </section>

        {/* Statuto Section */}
        <section className="py-16 bg-background">
          <div className="container max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{page?.sections && page.sections[4]?.title}</h2>
              <p className="text-lg text-muted-foreground">
                Il Club Aviazione Popolare è regolato da uno statuto che definisce gli obiettivi,
                i diritti e i doveri dei soci.
              </p>
            </div>

            <Card className="mission [&_h3]:text-xl [&_h3]:font-bold [&_h3]:mb-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:space-y-1">
              <CardContent className="p-8">
                <div className="space-y-6 prose">
                  <ReactMarkdown>
                    {page?.sections && page.sections[4]?.content}
                  </ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div >
  )
}
