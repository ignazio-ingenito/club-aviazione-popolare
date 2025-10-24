import { HeaderHome } from "@/components/header/home"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, ArrowRight, User } from "lucide-react"
import Link from "next/link"
import { getMetadata } from "@/lib/utils"

const newsArticles = [
  {
    id: "53-raduno-cap",
    date: { day: "26", month: "NOV", year: "2024" },
    title: "53° RADUNO CAP - BICIANCA (IMMAGINI)",
    category: "Eventi",
    author: "Redazione CAP",
    excerpt:
      "Galleria fotografica del 53° Raduno. Per vedere le foto scorrere la galleria cliccando sulle frecce. Un evento straordinario con oltre 60 partecipanti e condizioni meteo perfette per il volo.",
    image: "/raduno-cap-bicianca-2024.jpg",
    featured: true,
  },
  {
    id: "53-raduno-istruzioni",
    date: { day: "21", month: "OTT", year: "2024" },
    title: "53° RADUNO CAP - ISTRUZIONI PER IL VOLO",
    category: "Eventi",
    author: "Comitato Organizzatore",
    excerpt:
      "Domenica arriverà finalmente il giorno del 53° Raduno CAP che si terrà nel campo di Bicianca. Ecco tutte le informazioni necessarie per partecipare: orari, regolamento di volo e indicazioni logistiche.",
    image: "/campo-volo-bicianca.jpg",
    featured: false,
  },
  {
    id: "raduno-2025-last-minute",
    date: { day: "12", month: "OTT", year: "2024" },
    title: "RADUNO CAP 2025 - LAST MINUTE NEWS",
    category: "Annunci",
    author: "Presidente CAP",
    excerpt:
      "Mancano 2 Settimane al nostro Raduno e desidero far notare l'incredibile news (ormai storica) che quest'anno abbiamo raggiunto il record di iscrizioni. Ultimi posti disponibili!",
    image: "/raduno-preparation.jpg",
    featured: false,
  },
  {
    id: "estate-avventurosa",
    date: { day: "08", month: "SET", year: "2024" },
    title: "L'ESTATE AVVENTUROSA - NOTTURNO LUGLIO 2025",
    category: "Attività",
    author: "Marco Rossi",
    excerpt:
      "Con due ore di ritardo, giusto per il tempo di fare una cena veloce e preparare per due ore di volo notturno, siamo arrivati al campo. Un'esperienza magica sotto le stelle con aeromodelli illuminati.",
    image: "/volo-notturno-estate.jpg",
    featured: false,
  },
  {
    id: "corso-costruzione-primavera",
    date: { day: "15", month: "AGO", year: "2024" },
    title: "NUOVO CORSO DI COSTRUZIONE - PRIMAVERA 2025",
    category: "Corsi",
    author: "Istruttori CAP",
    excerpt:
      "Aperte le iscrizioni per il corso di costruzione primaverile. Impareremo a costruire un trainer completo partendo da zero, con tecniche tradizionali e moderne.",
    image: "/corso-costruzione.jpg",
    featured: false,
  },
  {
    id: "manutenzione-motori",
    date: { day: "02", month: "LUG", year: "2024" },
    title: "WORKSHOP: MANUTENZIONE MOTORI A SCOPPIO",
    category: "Tecnica",
    author: "Giuseppe Bianchi",
    excerpt:
      "Workshop tecnico dedicato alla manutenzione e messa a punto dei motori a scoppio. Dalla pulizia alla carburazione ottimale, tutti i segreti per prestazioni al top.",
    image: "/motori-aeromodelli.jpg",
    featured: false,
  },
]

export default async function NewsPage() {
  const meta = await getMetadata()

  const featuredArticle = newsArticles.find((article) => article.featured)
  const regularArticles = newsArticles.filter((article) => !article.featured)

  return (
    <div className="flex min-h-screen flex-col">
      <HeaderHome title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative py-20 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
          <div className="container">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">News e Aggiornamenti</h1>
            <p className="text-xl leading-relaxed max-w-3xl opacity-90">
              Resta aggiornato sulle ultime novità del Club Aviazione Popolare: eventi, corsi, attività e molto altro.
            </p>
          </div>
        </section>

        {/* Featured Article */}
        {featuredArticle && (
          <section className="py-16 bg-background">
            <div className="container">
              <Card className="overflow-hidden hover:shadow-xl transition-shadow">
                <div className="grid md:grid-cols-2 gap-0">
                  <div className="relative h-[400px] md:h-auto">
                    <img
                      src={featuredArticle.image || "/placeholder.svg"}
                      alt={featuredArticle.title}
                      className="w-full h-full object-cover"
                    />
                    <Badge className="absolute top-4 left-4 bg-secondary text-secondary-foreground">In Evidenza</Badge>
                  </div>
                  <CardContent className="p-8 flex flex-col justify-center">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>
                          {featuredArticle.date.day} {featuredArticle.date.month} {featuredArticle.date.year}
                        </span>
                      </div>
                      <Badge variant="outline">{featuredArticle.category}</Badge>
                    </div>
                    <h2 className="text-3xl font-bold mb-4 text-balance">{featuredArticle.title}</h2>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                      <User className="h-4 w-4" />
                      <span>{featuredArticle.author}</span>
                    </div>
                    <p className="text-lg text-muted-foreground leading-relaxed mb-6">{featuredArticle.excerpt}</p>
                    <Link
                      href={`/news/${featuredArticle.id}`}
                      className="inline-flex items-center text-primary font-medium hover:underline"
                    >
                      Leggi l'articolo completo
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </CardContent>
                </div>
              </Card>
            </div>
          </section>
        )}

        {/* Regular Articles Grid */}
        <section className="py-16 bg-muted/50">
          <div className="container">
            <h2 className="text-3xl font-bold mb-8">Tutte le News</h2>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {regularArticles.map((article) => (
                <Card
                  key={article.id}
                  className="overflow-hidden group hover:shadow-lg transition-shadow flex flex-col"
                >
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={article.image || "/placeholder.svg"}
                      alt={article.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <Badge className="absolute top-4 right-4 bg-background/90 text-foreground">
                      {article.category}
                    </Badge>
                  </div>
                  <CardContent className="p-6 flex flex-col flex-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <Calendar className="h-4 w-4" />
                      <span>
                        {article.date.day} {article.date.month} {article.date.year}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold mb-3 group-hover:text-primary transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <User className="h-4 w-4" />
                      <span>{article.author}</span>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4 flex-1 line-clamp-3">
                      {article.excerpt}
                    </p>
                    <Link
                      href={`/news/${article.id}`}
                      className="inline-flex items-center text-sm font-medium text-primary hover:underline"
                    >
                      Leggi di più
                      <ArrowRight className="ml-1 h-3 w-3" />
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter CTA */}
        <section className="py-16 bg-primary text-primary-foreground">
          <div className="container max-w-4xl text-center">
            <h2 className="text-3xl font-bold mb-6">Resta Sempre Aggiornato</h2>
            <p className="text-lg leading-relaxed mb-8 opacity-90">
              Iscriviti alla nostra newsletter per ricevere le ultime news, gli aggiornamenti sugli eventi e le offerte
              esclusive per i soci del CAP.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
              <input
                type="email"
                placeholder="La tua email"
                className="flex-1 px-4 py-3 rounded-md text-foreground bg-background/90 focus:outline-none focus:ring-2 focus:ring-secondary"
              />
              <button className="px-6 py-3 bg-secondary text-secondary-foreground rounded-md font-medium hover:bg-secondary/90 transition-colors">
                Iscriviti
              </button>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
