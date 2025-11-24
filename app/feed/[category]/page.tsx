import Link from 'next/link'
import { findAll } from 'domutils'
import { Element } from "domhandler"
import { parseDocument } from 'htmlparser2'
import { render as domRender } from "dom-serializer"

import { Header } from '@/components/header'
import { SiteFooter } from "@/components/site-footer"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { Card, CardContent } from '@/components/ui/card'
import { getClaim, getFeeds, getMenu, getMetadata, sanitizeHtml } from "@/lib/server"

import { Feed } from "../../../lib/types"

import { ArrowRight } from 'lucide-react'

interface Props {
    params: {
        category: string
    }
}

function parseContent(html: string) {
    const doc = parseDocument(html)

    const images = findAll(
        (el): el is Element => el instanceof Element && el.name === "img",
        doc.children
    )
    for (let i = 0; i < images.length; i++) {
        images[i].attribs.class = `${(images[i].attribs.class || "")} float-end ml-2 rounded-md object-cover ${i > 0 ? "hidden" : ""} `
        if (images[i].attribs.src) {
            const u = new URL(images[i].attribs.src)
            u.searchParams.set("width", "155")
            u.searchParams.set("height", "155")
            images[i].attribs.src = u.toString()
        }
    }

    const anchors = findAll(
        (el): el is Element => el instanceof Element && el.name === "a",
        doc.children
    )
    for (let i = 0; i < anchors.length; i++) {
        anchors[i].attribs.class = `${(anchors[i].attribs.class || "")} text-accent underline`
    }

    return domRender(doc)
}

export default async function index({ params }: Props) {
    const { category: id } = params

    const meta = await getMetadata()
    const menu = await getMenu()
    const rows = await getFeeds(id) as Feed[]
    const claim = getClaim(id)

    return (
        <div className="feed flex min-h-screen flex-col">
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
                        <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance capitalize">{id}</h1>
                        <div className="text-md leading-relaxed opacity-90">
                            <TextToParagraphs text={claim} />
                        </div>
                    </div>
                </section>

                {/* Page Section */}
                <section className="py-8 px-1 sm:px-4 bg-background">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 place-items-center">
                        {rows.map(({ id, category, title, date, content }) => (
                            <Card key={id} className="h-full max-w-[460px] transition-shadow border-0 dark:border shadow-sm hover:shadow-lg">
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4 mb-4">
                                        <div className="flex flex-col items-center justify-center bg-primary text-primary-foreground rounded-lg p-3 min-w-18">
                                            <span className="text-2xl font-bold leading-none">{date.getDate()}</span>
                                            <span className="text-xs uppercase">{date.toLocaleString('it', { month: "short" })}</span>
                                            <span className="text-xs uppercase">{date.getFullYear()}</span>
                                        </div>
                                        <div className="flex-1">
                                            <h1 className="font-bold text-xl text-muted-foreground mb-2">
                                                {title}
                                            </h1>
                                        </div>
                                    </div>
                                    <div className="h-56 min-h-56 text-sm text-muted-foreground overflow-hidden"
                                        dangerouslySetInnerHTML={{ __html: parseContent(sanitizeHtml(content ?? "")) }}
                                    />
                                    <div className="mt-2 mb-0 flex items-center justify-end text-sm font-medium text-primary">
                                        <Link key={id} href={`/feed/${category.id}/${id}`} className="text-sm font-medium text-primary inline-flex items-center">
                                            Leggi di più <ArrowRight className="ml-1 h-3 w-3" />
                                        </Link>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </section>
            </main>
            <SiteFooter />
        </div >
    )
}