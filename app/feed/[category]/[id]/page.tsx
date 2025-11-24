
import { findAll } from "domutils"
import { isTag, Element } from "domhandler"
import { parseDocument } from "htmlparser2"
import { render as domRender } from "dom-serializer"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"
import { getFeed, sanitizeHtml } from "@/lib/server"

import { Calendar, User } from "lucide-react"

import styles from "./styles.module.css"
interface Props {
    params: {
        id: string
    }
}

function parseContent(html: string) {
    const doc = parseDocument(html)

    // find all the img tags
    const images = findAll(
        (el): el is Element => el instanceof Element && el.name === "img",
        doc.children
    )

    for (let i = 0; i < images.length; i++) {
        const { parent } = images[i]
        if (parent && isTag(parent) && parent.name === "section")
            continue

        // set the classes for the first img
        if (!images[i].attribs.src)
            continue

        const u = new URL(images[i].attribs.src)
        u.searchParams.delete("height")
        if (i == 0) {
            u.searchParams.delete("width")
            images[i].attribs.class = "w-full pb-2"
        }
        else {
            u.searchParams.set("width", "500")
            images[i].attribs.class = "w-full sm:w-2/3 md:w-1/3 px-0 sm:px-4 py-2"
            images[i].attribs.class += i % 2 === 1 ? " sm:pr-0 float-right" : " sm:pl-0 float-left"
        }
        images[i].attribs.src = u.toString()

    }

    return domRender(doc)
}

export default async function index({ params }: Props) {
    const { id: id_feed } = params
    const { author, title, category, date, content } = await getFeed(id_feed)

    return (
        <>
            <PageHero title={category?.title} description={category?.description} />

            <div className="p-8 flex flex-col gap-y-8 max-w-7xl m-auto">
                <PageTitle title={title} icon="graduation-cap" />

                {
                    date &&
                    (
                        <div className="flex justify-end-safe text-sm">
                            <div className="grid grid-cols-[auto_1fr] gap-2 items-center">
                                <div>
                                    <Calendar className="size-5 text-accent" />
                                </div>
                                <div className="capitalize text-muted-foreground font-semibold text-right">
                                    {new Date(date).toLocaleString("it", {
                                        weekday: "short",
                                        year: "numeric",
                                        month: "short",
                                        day: "numeric",
                                    })}
                                </div>
                                <div>
                                    <User className="size-5 text-accent" />
                                </div>
                                <div className="capitalize text-muted-foreground font-semibold text-right">
                                    {author}
                                </div>
                            </div>
                        </div>
                    )
                }
                <div
                    className={`${styles.feeds} select-none text-muted-foreground`}
                    dangerouslySetInnerHTML={{ __html: parseContent(sanitizeHtml(content ?? "")) }}
                />
            </div >
        </>
    )
}
