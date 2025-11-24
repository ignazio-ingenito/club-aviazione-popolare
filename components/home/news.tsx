import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

import { ArrowRight } from "lucide-react"

const newsItems = [
    {
        date: { day: "26", month: "NOV" },
        title: "53° RADUNO CAP - BICIANCA (IMMAGINI)",
        excerpt: "Galleria fotografica del 53° Raduno. Per vedere le foto scorrere la galleria cliccando sulle frecce...",
        link: "/news/53-raduno-cap",
    },
    {
        date: { day: "21", month: "OTT" },
        title: "53° RADUNO CAP - ISTRUZIONI PER IL VOLO",
        excerpt: "Domenica arriverà finalmente il giorno del 53° Raduno CAP che si terrà nel campo di Bicianca...",
        link: "/news/53-raduno-istruzioni",
    },
    {
        date: { day: "12", month: "OTT" },
        title: "RADUNO CAP 2025 - LAST MINUTE NEWS",
        excerpt: "Mancano 2 Settimane al nostro Raduno e desidero far notare l'incredibile news (ormai storica) che...",
        link: "/news/raduno-2025-last-minute",
    },
    {
        date: { day: "08", month: "SET" },
        title: "L'ESTATE AVVENTUROSA - NOTTURNO LUGLIO 2025",
        excerpt: "Con due ore di ritardo, giusto per il tempo di fare una cena veloce e preparare per due...",
        link: "/news/estate-avventurosa",
    },
]

export const News = () => {
    return (
        <section className="pt-16 pb-8 px-4 bg-background">
            <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl md:text-4xl font-bold">Ultime News CAP</h2>
                <Button asChild variant="ghost">
                    <Link href="/news">
                        Vedi tutte
                        <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {newsItems.map((item, index) => (
                    <Card key={index} className="group hover:shadow-lg transition-shadow border-0 dark:border shadow-sm hover:cursor-pointer">
                        <Link
                            legacyBehavior
                            href={item.link}
                            className="text-sm font-medium text-primary inline-flex items-center"
                        >
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="flex flex-col items-center justify-center bg-primary text-primary-foreground rounded-lg p-3 min-w-[60px]">
                                        <span className="text-2xl font-bold leading-none">{item.date.day}</span>
                                        <span className="text-xs uppercase mt-1">{item.date.month}</span>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-bold text-sm leading-tight mb-2 group-hover:text-primary transition-colors">
                                            {item.title}
                                        </h3>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground leading-relaxed mb-4">{item.excerpt}</p>
                                </div>
                                <div className="absolute b-0 flex items-center text-sm font-medium text-primary">
                                    Leggi di più <ArrowRight className="ml-1 h-3 w-3" />
                                </div>
                            </CardContent>
                        </Link>
                    </Card>
                ))}
            </div>
        </section>
    )
}
