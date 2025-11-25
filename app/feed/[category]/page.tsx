import Link from 'next/link'

import { findAll } from 'domutils'
import { Element } from "domhandler"
import { parseDocument } from 'htmlparser2'
import { render as domRender } from "dom-serializer"

import { PageHero } from '@/components/page/hero'
import { Card, CardContent } from '@/components/ui/card'
import { getCategory, getFeeds, sanitizeHtml } from "@/lib/server"

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

    const rows = await getFeeds(id) as Feed[]
    const { title, description } = await getCategory(id)

    return (
        <>
            <PageHero title={title} description={description} />

            <div className="px-2 py-8 flex flex-col gap-y-8 max-w-7xl m-auto">
                <div className="pb-1 grid gap-4 grid-cols-[repeat(auto-fit,minmax(320px,360px))] justify-center overflow-hidden">
                    {rows.map(({ id, category, title, date, content }) => (
                        <Link key={id}
                            legacyBehavior
                            href={`/feed/${category.id}/${id}`} className="text-sm font-medium text-primary inline-flex items-center">
                            <Card key={id} className="h-full max-w-[460px] transition-shadow border-0 dark:border shadow-sm hover:shadow-lg hover:cursor-pointer">
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4 mb-4">
                                        <div className="flex flex-col items-center justify-center bg-primary text-primary-foreground rounded-lg p-3 min-w-18" data-date={date.toISOString().slice(0, 10)}>
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
                                    <p className="mt-2 mb-0 flex items-center justify-end text-sm font-medium text-primary">
                                        Leggi di più <ArrowRight className="ml-1 h-3 w-3" />
                                    </p>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            </div>
        </ >
    )
}