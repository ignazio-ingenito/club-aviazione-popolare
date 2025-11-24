import { SiteFooter } from "@/components/site-footer"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, sanitizeHtml } from "@/lib/server"

import { MapPinHouse } from "lucide-react"
import { Header } from '@/components/header'

interface Props {
    params: {
        key: string
    }
}

export default async function index({ params }: Props) {
    const key = "associazioni"
    const meta = await getMetadata()
    const menu = await getMenu()
    const page = await getPage(params.key)

    return (
        <div className={`${key} flex min-h-screen flex-col`}>
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

            <main className="flex-1 w-full max-w-7xl m-auto mb-8">
                {/* Hero Section */}
                <section className="relative pt-24 pb-6 mb-6 bg-linear-to-br from-primary to-primary/80 text-secondary-foreground">
                    <div className="container px-6 ">
                        <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">{page?.content_title}</h1>
                        <div className="text-lg leading-relaxed opacity-90">
                            <TextToParagraphs text={page.description ?? ""} />
                        </div>
                    </div>
                </section>

                <section className="px-8 min-[1300px]:px-0 bg-background">
                    <div className="flex items-center gap-3">
                        <MapPinHouse className="h-8 w-8" />
                        <h2 className="text-3xl font-bold pt-8 pb-3">{page?.content_title}</h2>
                    </div>
                    <p className="text-xl text-muted-foreground pb-8">
                        Scegli l'associazione più vicina a te per iniziare la tua avventura nella costruzione amatoriale
                    </p>
                </section>

                <section className="px-8 min-[1300px]:px-0 space-y-8">
                    <div className="text-muted-foreground text-md [&_img]:mr-4 [&_img]:pt-2 [&_img]:min-[600px]:float-left [&_img]:max-[600px]:mb-6 [&_h2]:text-2xl [&_h2]:not-first-of-type:pt-6 [&_h2]:pb-2"
                        dangerouslySetInnerHTML={{ __html: sanitizeHtml(page.content ?? "") }}
                    />
                </section>
            </main>
            <SiteFooter />
        </div >
    )
}
