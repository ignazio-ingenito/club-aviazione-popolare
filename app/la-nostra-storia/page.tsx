import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"
import { LucideIcon } from "@/components/lucide-icon"
import { PageSection } from "@/lib/types"
import { Card, CardContent } from "@/components/ui/card"
import { getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

const icons: string[] = ["users", "target", "file-text"]

export default async function index() {
  const { content, content_title, description, sections } = await getPage("la-nostra-storia")

  return (
    <>
      <PageHero title={content_title} description={description} />

      {/* Storia Section */}
      <div className="py-8 flex flex-col gap-y-8 max-w-5xl m-auto">
        <PageTitle title={content_title} description={description} icon="library-big" />

        <div
          className="text-muted-foreground select-none"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(content) }}
        />

        <section className="pb-8 px-8">
          <div className="w-full">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">{sections && sections[0].title}</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                {sections && sections[0].title}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {sections?.slice(1, 4).map(({ id, title, content }: PageSection, i) => (
                <Card key={id} data-id={id}>
                  <CardContent className="p-6">
                    <div className="flex flex-col items-center text-center">
                      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <LucideIcon name={icons[i % icons.length]} className="h-8 w-8 text-primary" />
                      </div>
                      <h3 className="text-xl font-bold mb-3">{title}</h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {content}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>
      </div>
    </>
  )
}