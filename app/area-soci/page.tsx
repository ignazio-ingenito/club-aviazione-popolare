"use client"

import type React from "react"

import { HeaderPage } from "@/components/header-page"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Lock, User, FileText, Calendar, Users, Award } from "lucide-react"
import { useState } from "react"
import { getMetadata } from "@/lib/utils"

export default async function AreaSociPage() {
  const [loginData, setLoginData] = useState({
    username: "",
    password: "",
  })
  const [error, setError] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!loginData.username || !loginData.password) {
      setError("Inserisci username e password")
      return
    }

    // Here you would typically authenticate with your backend
    console.log("Login attempt:", loginData)
    setError("Funzionalità di login non ancora implementata")
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setLoginData((prev) => ({ ...prev, [name]: value }))
    setError("")
  }

  const meta = await getMetadata()

  return (
    <div className="flex min-h-screen flex-col">
      <HeaderPage title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <section className="relative py-20 bg-linear-to-br from-primary to-primary/80 text-primary-foreground">
          <div className="container">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Area Soci</h1>
            <p className="text-xl leading-relaxed max-w-3xl opacity-90">
              Accedi all'area riservata per gestire la tua iscrizione, consultare documenti e partecipare alle attività
              del club.
            </p>
          </div>
        </section>

        {/* Login Section */}
        <section className="py-16 bg-background">
          <div className="container max-w-6xl">
            <div className="grid lg:grid-cols-2 gap-12 items-start">
              {/* Login Form */}
              <Card>
                <CardContent className="p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <Lock className="h-6 w-6 text-primary" />
                    </div>
                    <h2 className="text-2xl font-bold">Accedi</h2>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="username">Username o Email</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                          id="username"
                          name="username"
                          value={loginData.username}
                          onChange={handleChange}
                          placeholder="Il tuo username"
                          className="pl-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                          id="password"
                          name="password"
                          type="password"
                          value={loginData.password}
                          onChange={handleChange}
                          placeholder="La tua password"
                          className="pl-10"
                        />
                      </div>
                    </div>

                    {error && (
                      <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                        <p className="text-sm text-destructive">{error}</p>
                      </div>
                    )}

                    <Button type="submit" size="lg" className="w-full">
                      Accedi all'Area Riservata
                    </Button>

                    <div className="text-center">
                      <a href="#" className="text-sm text-primary hover:underline">
                        Password dimenticata?
                      </a>
                    </div>
                  </form>
                </CardContent>
              </Card>

              {/* Benefits Section */}
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold mb-4">Vantaggi dell'Area Soci</h2>
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    L'area riservata ti permette di accedere a contenuti esclusivi e gestire la tua partecipazione alle
                    attività del club.
                  </p>
                </div>

                <div className="space-y-4">
                  <Card>
                    <CardContent className="p-4 flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-1">Documenti Riservati</h3>
                        <p className="text-sm text-muted-foreground">
                          Accedi a statuto, regolamenti, verbali e documentazione tecnica del club.
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Calendar className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-1">Calendario Eventi</h3>
                        <p className="text-sm text-muted-foreground">
                          Visualizza il calendario completo e iscriviti agli eventi riservati ai soci.
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Users className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-1">Forum e Comunità</h3>
                        <p className="text-sm text-muted-foreground">
                          Partecipa alle discussioni, condividi esperienze e chiedi consigli agli altri soci.
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Award className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-1">Gestione Iscrizione</h3>
                        <p className="text-sm text-muted-foreground">
                          Rinnova la tua iscrizione, aggiorna i tuoi dati e consulta lo storico delle attività.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Membership Info */}
        <section className="py-16 bg-muted/50">
          <div className="container max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Non Sei Ancora Socio?</h2>
              <p className="text-lg text-muted-foreground">
                Unisciti al Club Aviazione Popolare e scopri il mondo dell'aeromodellismo insieme a noi.
              </p>
            </div>

            <Card>
              <CardContent className="p-8">
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-xl font-bold mb-4">Come Diventare Socio</h3>
                    <ul className="space-y-3 text-muted-foreground">
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">1.</span>
                        <span>Compila il modulo di iscrizione disponibile in segreteria o online</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">2.</span>
                        <span>Effettua il pagamento della quota associativa annuale</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">3.</span>
                        <span>Ottieni il tesseramento presso l'Aeroclub d'Italia</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">4.</span>
                        <span>Ricevi le credenziali per accedere all'area riservata</span>
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-xl font-bold mb-4">Requisiti</h3>
                    <ul className="space-y-3 text-muted-foreground mb-6">
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>Maggiore età o autorizzazione dei genitori per i minorenni</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>Passione per l'aviazione e l'aeromodellismo</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>Rispetto del regolamento interno del club</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>Tesseramento presso ente riconosciuto (Aeroclub d'Italia)</span>
                      </li>
                    </ul>

                    <Button asChild size="lg" className="w-full">
                      <a href="/contatti">Richiedi Informazioni</a>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
