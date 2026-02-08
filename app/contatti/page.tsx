import type React from "react"

import { Card, CardContent } from "@/components/ui/card"
import { Mail, Phone, MapPin, Clock, Facebook, Twitter, Instagram, Info, MapPinCheck } from "lucide-react"
import { getMetadata, getPage } from "@/lib/server"
import { PageHero } from "@/components/page/hero"

import GoogleMap from "./google-map"
import OpenStreetMap from "./openstreet-map"
import FormContacts from "./form"

export default async function index() {
  const { address, email, facebook, instagram, map_type, phone, twitter } = await getMetadata()
  const { title, description } = await getPage("contatti")

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          {/* Contact Info and Form */}
          <section>
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
                        <h5 className="text-muted-foreground font-bold mb-2">Telefono</h5>
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
                        <h5 className="text-muted-foreground font-bold mb-2">Email</h5>
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
                        <h5 className="text-muted-foreground font-bold mb-2">Indirizzo</h5>
                        <div className="text-muted-foreground text-sm">
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
                        <h5 className="text-muted-foreground font-bold mb-2">Orari Segreteria</h5>
                        <div className="text-muted-foreground">
                          <span className="mb-1 text-sm">Gli uffici di Bresso sono aperti</span>
                          <div className="grid grid-cols-2 mt-1 text-sm">
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
                    <div className="w-full flex justify-center items-center">
                      <h5 className="text-muted-foreground font-bold mb-4">Seguici sui Social</h5>
                    </div>
                    <div className="flex justify-center gap-4 transition-all ease-in-out duration-700">
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
              <div className="lg:col-span-2 flex flex-col gap-y-3">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Info className="h-6 w-6 text-primary" />
                      </div>
                      <div className="text-muted-foreground leading-6.75">
                        In questo sito sono elencate le <a href="/le-nostre-sezioni" className="underline text-accent">associazioni affiliate</a> al Sodalizio CAP.<br />
                        A loro potete rivolgervi per avere aiuto e trovare vicino a voi chi vi può aiutare per un nuovo progetto di costruzione amatoriale.
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-8">
                    <h5 className="text-2xl font-bold mb-6 text-muted-foreground">Invia un Messaggio</h5>
                    <div className="contatti-form">
                      <FormContacts />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          <section>
            <Card>
              <CardContent>
                <div className="w-full flex items-center gap-x-4 my-6">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <MapPinCheck className="h-6 w-6 text-primary" />
                  </div>
                  <h5 className="text-2xl font-bold m-0 text-muted-foreground">
                    Come Raggiungerci
                  </h5>
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
        </div>
      </div >
    </>
  )
}
