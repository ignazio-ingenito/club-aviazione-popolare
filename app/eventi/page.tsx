import { Header } from "@/components/header"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, MapPin, Clock, Users } from "lucide-react"
import { getMetadata } from "@/lib/server"

const upcomingEvents = [
  {
    title: "54° Raduno CAP 2025",
    date: "15 Giugno 2025",
    time: "09:00 - 18:00",
    location: "Campo di Volo Bicianca, Monza",
    description:
      "Il tradizionale raduno annuale del club con gare di volo, esibizioni e premiazioni. Aperto a tutti i soci e agli appassionati.",
    status: "upcoming",
    participants: "50+ partecipanti attesi",
  },
  {
    title: "Corso di Costruzione Base",
    date: "5 Maggio 2025",
    time: "14:00 - 18:00",
    location: "Sede CAP, Monza",
    description:
      "Corso introduttivo alla costruzione di aeromodelli per principianti. Materiali e strumenti forniti dal club.",
    status: "upcoming",
    participants: "Posti limitati",
  },
  {
    title: "Volo Notturno Estivo",
    date: "20 Luglio 2025",
    time: "20:00 - 23:00",
    location: "Campo di Volo Bicianca",
    description:
      "Serata speciale di volo notturno con aeromodelli illuminati. Un'esperienza unica per i soci del club.",
    status: "upcoming",
    participants: "Aperto ai soci",
  },
]

const pastEvents = [
  {
    title: "53° Raduno CAP - Bicianca",
    date: "26 Novembre 2024",
    location: "Campo di Volo Bicianca",
    image: "/model-aircraft-gathering-event.jpg",
    description: "Grande successo per il 53° raduno con oltre 60 partecipanti e condizioni meteo perfette.",
  },
  {
    title: "L'Estate Avventurosa - Volo Notturno",
    date: "8 Settembre 2024",
    location: "Campo di Volo Bicianca",
    image: "/night-flying-model-aircraft-with-lights.jpg",
    description: "Serata magica di volo notturno con aeromodelli illuminati sotto le stelle.",
  },
  {
    title: "Corso Avanzato di Acrobazia",
    date: "15 Giugno 2024",
    location: "Sede CAP",
    image: "/aerobatic-model-aircraft-in-flight.jpg",
    description: "Workshop intensivo sulle tecniche di volo acrobatico con istruttori esperti.",
  },
]

export default async function EventiPage() {
  const meta = await getMetadata()
  return (
    <div className="flex min-h-screen flex-col">
      <Header title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-5xl m-auto">
        {/* Hero Section */}
        <section className="relative py-20 bg-linear-to-br from-primary to-primary/80 text-primary-foreground">
          <div className="container">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Eventi e Attività</h1>
            <p className="text-xl leading-relaxed max-w-3xl opacity-90">
              Scopri i prossimi eventi del Club Aviazione Popolare: raduni, corsi di formazione, gare e molto altro.
            </p>
          </div>
        </section>

        {/* Upcoming Events */}
        <section className="py-16 bg-background">
          <div className="container">
            <div className="mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Prossimi Eventi</h2>
              <p className="text-lg text-muted-foreground">
                Partecipa alle nostre attività e vivi la passione per l'aeromodellismo insieme a noi.
              </p>
            </div>

            <div className="grid gap-8">
              {upcomingEvents.map((event, index) => (
                <Card key={index} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <CardContent className="p-0">
                    <div className="grid md:grid-cols-[200px_1fr] gap-0">
                      <div className="bg-primary text-primary-foreground p-6 flex flex-col justify-center items-center text-center">
                        <Calendar className="h-12 w-12 mb-3" />
                        <div className="text-2xl font-bold">{event.date.split(" ")[0]}</div>
                        <div className="text-sm opacity-90">
                          {event.date.split(" ")[1]} {event.date.split(" ")[2]}
                        </div>
                      </div>
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="text-2xl font-bold">{event.title}</h3>
                          <Badge variant="secondary" className="ml-2">
                            In arrivo
                          </Badge>
                        </div>
                        <div className="space-y-2 mb-4">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span className="text-sm">{event.time}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <MapPin className="h-4 w-4" />
                            <span className="text-sm">{event.location}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Users className="h-4 w-4" />
                            <span className="text-sm">{event.participants}</span>
                          </div>
                        </div>
                        <p className="text-muted-foreground leading-relaxed">{event.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Past Events Gallery */}
        <section className="py-16 bg-muted/50">
          <div className="container">
            <div className="mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Eventi Passati</h2>
              <p className="text-lg text-muted-foreground">
                Rivivi i momenti più belli delle nostre attività attraverso foto e racconti.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {pastEvents.map((event, index) => (
                <Card key={index} className="overflow-hidden group hover:shadow-lg transition-shadow">
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={event.image || "/placeholder.svg"}
                      alt={event.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <Calendar className="h-4 w-4" />
                      <span>{event.date}</span>
                    </div>
                    <h3 className="text-xl font-bold mb-2">{event.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <MapPin className="h-4 w-4" />
                      <span>{event.location}</span>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">{event.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Calendar Info */}
        <section className="py-16 bg-background">
          <div className="container max-w-4xl text-center">
            <h2 className="text-3xl font-bold mb-6">Calendario Completo</h2>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Per accedere al calendario completo degli eventi, alle iscrizioni e ai dettagli riservati ai soci,
              effettua il login nell'area riservata.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/area-soci"
                className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Accedi all'Area Soci
              </a>
              <a
                href="/contatti"
                className="inline-flex items-center justify-center rounded-md border border-input bg-background px-8 py-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Diventa Socio
              </a>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
