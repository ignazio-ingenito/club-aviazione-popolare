import { Header } from "@/components/header"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plane, Ruler, Weight, Calendar } from "lucide-react"
import { getMetadata } from "@/lib/utils"

const aircraft = [
  {
    name: "Piper J-3 Cub",
    category: "Trainer",
    image: "/yellow-piper-cub-model-aircraft.jpg",
    specs: {
      wingspan: "2.40 m",
      length: "1.65 m",
      weight: "3.2 kg",
      engine: "OS 46 FX",
      year: "2018",
    },
    description:
      "Perfetto per i principianti, il Piper Cub è un classico dell'aviazione leggera. Stabile e facile da pilotare, ideale per i primi voli.",
  },
  {
    name: "Spitfire Mk IX",
    category: "Warbird",
    image: "/spitfire-model-aircraft-in-flight.jpg",
    specs: {
      wingspan: "1.98 m",
      length: "1.72 m",
      weight: "4.5 kg",
      engine: "Saito 120",
      year: "2020",
    },
    description:
      "Replica fedele del leggendario caccia britannico della Seconda Guerra Mondiale. Prestazioni acrobatiche eccellenti.",
  },
  {
    name: "Extra 300",
    category: "Acrobatico",
    image: "/extra-300-aerobatic-model-aircraft.jpg",
    specs: {
      wingspan: "1.80 m",
      length: "1.55 m",
      weight: "3.8 kg",
      engine: "DLE 30",
      year: "2021",
    },
    description:
      "Aeromodello acrobatico ad alte prestazioni. Progettato per manovre 3D e acrobazie avanzate con potenza e precisione.",
  },
  {
    name: "Cessna 182 Skylane",
    category: "Trainer",
    image: "/cessna-182-model-aircraft.jpg",
    specs: {
      wingspan: "2.20 m",
      length: "1.50 m",
      weight: "3.5 kg",
      engine: "OS 55 AX",
      year: "2019",
    },
    description:
      "Aeromodello versatile e affidabile, perfetto per voli di durata e addestramento avanzato. Eccellente stabilità.",
  },
  {
    name: "P-51 Mustang",
    category: "Warbird",
    image: "/p51-mustang-model-aircraft.jpg",
    specs: {
      wingspan: "2.10 m",
      length: "1.80 m",
      weight: "5.2 kg",
      engine: "Saito 150",
      year: "2017",
    },
    description:
      "Icona dell'aviazione militare americana. Linee eleganti e prestazioni straordinarie per un volo realistico.",
  },
  {
    name: "Pitts Special S-2B",
    category: "Acrobatico",
    image: "/pitts-special-biplane-model.jpg",
    specs: {
      wingspan: "1.65 m",
      length: "1.40 m",
      weight: "3.0 kg",
      engine: "OS 46 LA",
      year: "2022",
    },
    description:
      "Biplano acrobatico leggendario. Agilità estrema e capacità acrobatiche impressionanti per piloti esperti.",
  },
]

export default async function FlottaPage() {
  const meta = await getMetadata()
  return (
    <div className="flex min-h-screen flex-col">
      <Header title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative py-20 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
          <div className="container">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">La Nostra Flotta</h1>
            <p className="text-xl leading-relaxed max-w-3xl opacity-90">
              Scopri gli aeromodelli del Club Aviazione Popolare: dai trainer per principianti ai warbird storici e agli
              acrobatici ad alte prestazioni.
            </p>
          </div>
        </section>

        {/* Fleet Grid */}
        <section className="py-16 bg-background">
          <div className="container">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {aircraft.map((plane, index) => (
                <Card key={index} className="overflow-hidden group hover:shadow-xl transition-all">
                  <div className="relative h-64 overflow-hidden bg-muted">
                    <img
                      src={plane.image || "/placeholder.svg"}
                      alt={plane.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    <Badge className="absolute top-4 right-4 bg-secondary text-secondary-foreground">
                      {plane.category}
                    </Badge>
                  </div>
                  <CardContent className="p-6">
                    <h3 className="text-2xl font-bold mb-3 group-hover:text-primary transition-colors">{plane.name}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4">{plane.description}</p>

                    <div className="space-y-2 border-t pt-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-muted-foreground">
                          <Ruler className="h-4 w-4" />
                          Apertura alare
                        </span>
                        <span className="font-medium">{plane.specs.wingspan}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-muted-foreground">
                          <Plane className="h-4 w-4" />
                          Lunghezza
                        </span>
                        <span className="font-medium">{plane.specs.length}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-muted-foreground">
                          <Weight className="h-4 w-4" />
                          Peso
                        </span>
                        <span className="font-medium">{plane.specs.weight}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Motore</span>
                        <span className="font-medium">{plane.specs.engine}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-muted-foreground">
                          <Calendar className="h-4 w-4" />
                          Anno
                        </span>
                        <span className="font-medium">{plane.specs.year}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Categories Info */}
        <section className="py-16 bg-muted/50">
          <div className="container">
            <h2 className="text-3xl md:text-4xl font-bold mb-12 text-center">Categorie di Aeromodelli</h2>

            <div className="grid md:grid-cols-3 gap-8">
              <Card>
                <CardContent className="p-6">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Plane className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">Trainer</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    Aeromodelli stabili e facili da pilotare, ideali per principianti e per l'addestramento.
                    Caratterizzati da ali alte e comportamento di volo prevedibile.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Plane className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">Warbird</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    Repliche di aerei militari storici della Seconda Guerra Mondiale e oltre. Combinano estetica storica
                    con prestazioni di volo realistiche.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Plane className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">Acrobatico</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    Aeromodelli ad alte prestazioni progettati per manovre acrobatiche avanzate e volo 3D. Richiedono
                    esperienza e abilità di pilotaggio.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-background">
          <div className="container max-w-4xl text-center">
            <h2 className="text-3xl font-bold mb-6">Vuoi Costruire il Tuo Aeromodello?</h2>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Il CAP organizza corsi di costruzione per tutti i livelli. Impara le tecniche di costruzione tradizionale
              e moderna con l'aiuto di istruttori esperti.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/contatti"
                className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Iscriviti ai Corsi
              </a>
              <a
                href="/chi-siamo"
                className="inline-flex items-center justify-center rounded-md border border-input bg-background px-8 py-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Scopri di Più
              </a>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
