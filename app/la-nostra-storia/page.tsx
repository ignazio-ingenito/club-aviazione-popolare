import { findAll } from "domutils"
import { Element } from "domhandler"
import { parseDocument } from "htmlparser2"
import { render as domRender } from "dom-serializer"


import { getPage, sanitizeHtml } from "@/lib/server"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"
import { Card, CardContent } from "@/components/ui/card"
import { PageSection } from "@/lib/types"
import { LucideIcon } from "@/components/lucide-icon"

const icons: string[] = ["users", "target", "file-text"]

function parseContent(html: string) {
  const doc = parseDocument(html)

  // find all the img tags
  const images = findAll(
    (el): el is Element => el instanceof Element && el.name === "img",
    doc.children
  )

  images.forEach((img, n) => {
    // set the classes for the first img
    if (n == 0) {
      img.attribs.class += `${img.attribs.class} pb-4 w-full`
      return
    }

    // set the float-left and right accordingly
    img.attribs.class = "w-full sm:w-auto p-4"
    img.attribs.class += n % 2 === 1 ? " pr-0 float-right" : " pl-0 float-left"
  })

  return domRender(doc)
}

export default async function index() {
  const { content, content_title, description, sections } = await getPage("la-nostra-storia")

  return (
    <>
      <PageHero title={content_title} description={description} />

      {/* Storia Section */}
      <div className="p-8 flex flex-col gap-y-8 max-w-7xl m-auto">
        <PageTitle title={content_title} description={description} icon="library-big" />

        <div
          className={`select - none text - muted - foreground`}
          dangerouslySetInnerHTML={{ __html: parseContent(sanitizeHtml(content ?? "")) }}
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