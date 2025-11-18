import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { TextToParagraphs } from "@/components/text-to-paragraphs"
import { getMetadata, getMenu, getPage, getChapters } from "@/lib/server"

import { Users, MapPinHouse, MapPin, Plane, GraduationCap, ClockFading, Globe, CalendarClock } from "lucide-react"
import { Header } from '@/components/header'
import Markdown from "react-markdown"

export default async function index() {
    const key = "associazioni"
    const meta = await getMetadata()
    const menu = await getMenu()
    const page = await getPage(key)
    const chapters = await getChapters()

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

                <section className="px-8 bg-background">
                    <div className="flex items-center gap-3">
                        <MapPinHouse className="h-8 w-8" />
                        <h2 className="text-3xl font-bold pt-8 pb-3">{page?.content_title}</h2>
                    </div>
                    <p className="text-xl text-muted-foreground pb-8">
                        Scegli l'associazione più vicina a te per iniziare la tua avventura nella costruzione amatoriale
                    </p>

                </section>

                <section className="space-y-8">
                    <div className="grid gap-6 lg:grid-cols-2 px-8 min-[1300px]:px-0">
                        {chapters.map(({ aircrafts, description, link, name, founded, location, members, president, website }) => (
                            <Card key={name} className="border-0 shadow-sm dark:border py-6 px-8">
                                <CardHeader className="p-0 m-0">
                                    <CardTitle className="text-2xl pb-3 border-b border-accent/20">
                                        <div className="flex flex-col sm:flex-row">
                                            <div>{name}</div>
                                            <a href={link} className="flex-1 flex gap-x-1 justify-start sm:justify-end items-center pt-2 sm:pt-0">
                                                <CalendarClock className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                                                <div className="text-sm font-normal text-accent hover:underline">
                                                    La nostra storia...
                                                </div>
                                            </a>
                                        </div>
                                    </CardTitle>
                                    <CardDescription className="flex [&_a]:text-accent [&_a]:pl-3">
                                        <Markdown>
                                            {description}
                                        </Markdown>
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="grid grid-cols-2 p-0 pt-4 gap-y-4">
                                    <div className="flex flex-col">
                                        <div className="flex gap-x-3 items-center">
                                            <Globe className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                            <h4 className="font-semibold text-sm">Sito web</h4>
                                        </div>
                                        <a
                                            href={`http://${website}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="pl-8 text-primary hover:underline"
                                        >
                                            {(website || "").replaceAll(/https?:\/\//g, "").replace(/\/.*$/, "")}
                                        </a>
                                    </div>
                                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-0.5 items-center">
                                        <ClockFading className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                        <h4 className="font-semibold text-sm">Fondato</h4>
                                        <p></p>
                                        <p className="text-sm text-muted-foreground">{founded}</p>
                                    </div>
                                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                                        <MapPin className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                        <h4 className="font-semibold text-sm">Sede</h4>
                                        <p></p>
                                        <p className="text-sm text-muted-foreground">{location}</p>
                                    </div>
                                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                                        <GraduationCap className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                        <h4 className="font-semibold text-sm">Presidente</h4>
                                        <p></p>
                                        <p className="text-sm text-muted-foreground">{president}</p>
                                    </div>
                                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                                        <Users className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                        <h4 className="font-semibold text-sm">Soci</h4>
                                        <p></p>
                                        <p className="text-sm text-muted-foreground">{members}</p>
                                    </div>
                                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                                        <Plane className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                                        <h4 className="font-semibold text-sm">Flotta</h4>
                                        <p></p>
                                        <p className="text-sm text-muted-foreground">{aircrafts}</p>
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
