import ReactMarkdown from 'react-markdown'
import { SiteFooter } from "@/components/site-footer"
import { HeaderPage } from "@/components/header-page"
import { Card, CardContent } from "@/components/ui/card"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getPage, getPageSections, sanitizeHtml } from "@/lib/utils"

import { Users, Target, FileText, History, LucideIcon } from "lucide-react"

const icons: LucideIcon[] = [Users, Target, FileText]

export default async function index() {
  const meta = await getMetadata()
  const page = await getPage("la-storia-del-cap")
  const secs = await getPageSections("la-storia-del-cap")


  return (
    <div className="chi-siamo flex min-h-screen flex-col">
      <HeaderPage title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative py-20 bg-gradient-to-br from-primary to-primary/80 text-secondary-foreground">
          <div className="container">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Chi Siamo</h1>
            <div className="text-lg leading-relaxed max-w-3xl opacity-90">
              <TextToParagraphs text={page.description ?? ""} />
            </div>
          </div>
        </section>

        {/* Storia Section */}
        <section className="py-16 bg-background">
          <div className="container">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <History className="h-8 w-8 text-primary" />
                <h2 className="text-3xl font-bold">{page?.content_title}</h2>
              </div>
              <div className="space-y-4 text-lg leading-relaxed text-muted-foreground" dangerouslySetInnerHTML={{ __html: sanitizeHtml(page.content ?? "") }} />
            </div>
          </div>
        </section>

        {/* Missione e Valori */}
        <section className="py-16 bg-muted/50">
          <div className="container">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{secs[0].title}</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                {secs[0].content}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {secs.slice(1, 4).map((sec, i) => {
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
          <div className="container max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{secs[4] && secs[4]?.title}</h2>
              <p className="text-lg text-muted-foreground">
                Il Club Aviazione Popolare è regolato da uno statuto che definisce gli obiettivi,
                i diritti e i doveri dei soci.
              </p>
            </div>

            <Card className="mission">
              <CardContent className="p-8">
                <div className="space-y-6 prose">
                  <ReactMarkdown>
                    {secs[4] && secs[4].content}
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
