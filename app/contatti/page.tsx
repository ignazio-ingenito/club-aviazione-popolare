
import type React from "react"
import dynamic from "next/dynamic"

import { Header } from "@/components/header"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Mail, Phone, MapPin, Clock, Facebook, Twitter, Instagram, Info, Megaphone, MapPinCheck } from "lucide-react"
import { getMenu, getMetadata, getPage } from "@/lib/server"
import { TextToParagraphs } from "@/components/text-to-paragraphs"




const FormContacts = dynamic(() => import("./form"), { ssr: false })
const GoogleMap = dynamic(() => import("./google-map"), { ssr: false })
const OpenStreetMap = dynamic(() => import("./openstreet-map"), { ssr: false })

export default async function index() {
  const key = "contatti"
  const menu = await getMenu()
  const {
    address,
    description,
    email,
    facebook,
    instagram,
    map_type,
    phone,
    title,
    twitter,
  } = await getMetadata()
  const page = await getPage(key)

  return (
    <div className="contattaci flex min-h-screen flex-col">
      <Header
        title={title}
        description={description}
        menu={menu}
        phone={phone}
        email={email}
        facebookUrl={facebook}
        instagramUrl={instagram}
        twitterUrl={twitter}
      />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative pt-24 pb-6 mb-6 bg-linear-to-br from-primary to-primary/80 text-secondary-foreground">
          <div className="container px-6">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">{page?.content_title}</h1>
            <div className="text-md leading-relaxed opacity-90">
              <TextToParagraphs text={page.description ?? ""} />
            </div>
          </div>
        </section>

        <section className="px-8 bg-background">
          <div className="flex items-center gap-3">
            <Megaphone className="h-8 w-8" />
            <h2 className="text-3xl font-bold py-8">{page?.content_title}</h2>
          </div>
        </section>

        {/* Contact Info and Form */}
        <section className="px-8 min-[1300px]:px-0 bg-background">
          <div className="grid lg:grid-cols-3 gap-4">
            {/* Contact Information */}
            <div className="grid grid-cols-1 gap-y-3 w-full lg:col-span-1">
              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Phone className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-2">Telefono</h3>
                      <a
                        href="tel:+39026107142"
                        className="text-muted-foreground hover:text-primary transition-colors"
                      >
                        {phone}
                      </a>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Mail className="h-6 w-6 text-primary" />
                    </div>
                    <div className="overflow-hidden text-ellipsis">
                      <h3 className="font-bold mb-2">Email</h3>
                      <a
                        href="mailto:segreteria@clubaviazionepopolare.org"
                        className="text-muted-foreground hover:text-primary transition-colors text-base min-[1024px]:text-sm"
                      >
                        {email}
                      </a>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <MapPin className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-2">Indirizzo</h3>
                      <div className="text-muted-foreground">
                        {(address || "")?.replaceAll(" - ", "<br />")}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Clock className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-2">Orari Segreteria</h3>
                      <div className="text-muted-foreground">
                        <span className="mb-1 text-sm">Gli uffici di Bresso sono aperti</span>
                        <div className="grid grid-cols-2 mt-1">
                          <div>Lunedì</div>
                          <div>10:00 - 16:00</div>
                          <div>Mercoledì</div>
                          <div>10:00 - 16:00</div>
                          <div>Venerdì</div>
                          <div>10:00 - 16:00</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="h-full">
                <CardContent className="p-6">
                  <h3 className="font-bold mb-4">Seguici sui Social</h3>
                  <div className="flex gap-4 transition-all ease-in-out duration-700">
                    {instagram && (
                      <a
                        href={instagram}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary hover:text-primary-foreground hover:bg-primary"
                        aria-label="Apri Twitter"
                      >
                        <Instagram className="h-4 w-4" />
                      </a>
                    )}
                    {facebook && (
                      <a
                        href={facebook}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary hover:text-primary-foreground hover:bg-primary"
                        aria-label="Apri Facebook"
                      >
                        <Facebook className="h-4 w-4" />
                      </a>
                    )}
                    {twitter && (
                      <a
                        href={twitter}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary hover:text-primary-foreground hover:bg-primary"
                        aria-label="Apri Twitter"
                      >
                        <Twitter className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2 flex flex-col gap-y-4">
              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Info className="h-6 w-6 text-primary" />
                    </div>
                    <div className="text-muted-foreground">
                      In questo sito sono elencate le <a href="/le-nostre-sezioni" className="underline text-accent">associazioni affiliate</a> al Sodalizio CAP.<br />
                      A loro potete rivolgervi per avere aiuto e trovare vicino a voi chi vi può aiutare per un nuovo progetto di costruzione amatoriale.
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-8">
                  <h2 className="text-2xl font-bold mb-6">Invia un Messaggio</h2>
                  <div className="contatti-form">
                    <FormContacts />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="pt-4 pb-8 px-8 min-[1300px]:px-0">
          <Card>
            <CardContent className="px-0 pb-0">
              <div className="w-full flex justify-center items-center gap-x-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <MapPinCheck className="h-6 w-6 text-primary" />
                </div>
                <h2 className="py-8 text-3xl font-bold text-center">
                  Come Raggiungerci
                </h2>
              </div>
              {/* Google Map Section */}
              <div className="rounded-b-lg overflow-hidden">
                {map_type == "google" &&
                  <GoogleMap />
                }
                {/* Leaflet Map Section */}
                {map_type == "openstreetmap" &&
                  <OpenStreetMap />
                }
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      <SiteFooter />
    </div >
  )
}
