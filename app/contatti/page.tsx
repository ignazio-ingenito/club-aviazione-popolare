"use client"

import type React from "react"

import { HeaderHome } from "@/components/header-home-cli"
import { SiteFooter } from "@/components/site-footer"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Mail, Phone, MapPin, Clock, Facebook, Twitter } from "lucide-react"
import { useState } from "react"
import { getMetadata } from "@/lib/utils"

export default async function ContattiPage() {

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    subject: "",
    message: "",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = "Il nome è obbligatorio"
    }

    if (!formData.email.trim()) {
      newErrors.email = "L'email è obbligatoria"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Inserisci un'email valida"
    }

    if (!formData.subject.trim()) {
      newErrors.subject = "L'oggetto è obbligatorio"
    }

    if (!formData.message.trim()) {
      newErrors.message = "Il messaggio è obbligatorio"
    } else if (formData.message.trim().length < 10) {
      newErrors.message = "Il messaggio deve contenere almeno 10 caratteri"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (validateForm()) {
      // Here you would typically send the form data to your backend
      console.log("Form submitted:", formData)
      setSubmitted(true)
      setFormData({ name: "", email: "", phone: "", subject: "", message: "" })
      setTimeout(() => setSubmitted(false), 5000)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }))
    }
  }

  const meta = await getMetadata()

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
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Contattaci</h1>
            <p className="text-xl leading-relaxed max-w-3xl opacity-90">
              Hai domande o vuoi unirti al Club Aviazione Popolare? Siamo qui per aiutarti. Contattaci tramite il form o
              utilizzando i nostri recapiti.
            </p>
          </div>
        </section>

        {/* Contact Info and Form */}
        <section className="py-16 bg-background">
          <div className="container">
            <div className="grid lg:grid-cols-3 gap-8">
              {/* Contact Information */}
              <div className="lg:col-span-1 space-y-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Phone className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-2">Telefono</h3>
                        <a
                          href="tel:+393518787742"
                          className="text-muted-foreground hover:text-primary transition-colors"
                        >
                          +39 351 878 7742
                        </a>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Mail className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-2">Email</h3>
                        <a
                          href="mailto:segreteria@clubaviazionepopolare.org"
                          className="text-muted-foreground hover:text-primary transition-colors break-all"
                        >
                          segreteria@clubaviazionepopolare.org
                        </a>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <MapPin className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-2">Indirizzo</h3>
                        <p className="text-muted-foreground">
                          Campo di Volo Bicianca
                          <br />
                          Monza (MB)
                          <br />
                          Italia
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Clock className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold mb-2">Orari Segreteria</h3>
                        <p className="text-muted-foreground text-sm">
                          Lunedì - Venerdì: 15:00 - 19:00
                          <br />
                          Sabato: 09:00 - 12:00
                          <br />
                          Domenica: Chiuso
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <h3 className="font-bold mb-4">Seguici sui Social</h3>
                    <div className="flex gap-4">
                      <a
                        href="https://facebook.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center hover:bg-primary hover:text-primary-foreground transition-colors"
                      >
                        <Facebook className="h-5 w-5" />
                      </a>
                      <a
                        href="https://twitter.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center hover:bg-primary hover:text-primary-foreground transition-colors"
                      >
                        <Twitter className="h-5 w-5" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Contact Form */}
              <div className="lg:col-span-2">
                <Card>
                  <CardContent className="p-8">
                    <h2 className="text-2xl font-bold mb-6">Invia un Messaggio</h2>

                    {submitted && (
                      <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                        <p className="text-green-800 dark:text-green-200">
                          Grazie per averci contattato! Ti risponderemo al più presto.
                        </p>
                      </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="name">
                            Nome e Cognome <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="Mario Rossi"
                            className={errors.name ? "border-destructive" : ""}
                          />
                          {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="email">
                            Email <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="mario.rossi@email.com"
                            className={errors.email ? "border-destructive" : ""}
                          />
                          {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="phone">Telefono (opzionale)</Label>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={formData.phone}
                          onChange={handleChange}
                          placeholder="+39 123 456 7890"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="subject">
                          Oggetto <span className="text-destructive">*</span>
                        </Label>
                        <Input
                          id="subject"
                          name="subject"
                          value={formData.subject}
                          onChange={handleChange}
                          placeholder="Richiesta informazioni iscrizione"
                          className={errors.subject ? "border-destructive" : ""}
                        />
                        {errors.subject && <p className="text-sm text-destructive">{errors.subject}</p>}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="message">
                          Messaggio <span className="text-destructive">*</span>
                        </Label>
                        <Textarea
                          id="message"
                          name="message"
                          value={formData.message}
                          onChange={handleChange}
                          placeholder="Scrivi qui il tuo messaggio..."
                          rows={6}
                          className={errors.message ? "border-destructive" : ""}
                        />
                        {errors.message && <p className="text-sm text-destructive">{errors.message}</p>}
                      </div>

                      <Button type="submit" size="lg" className="w-full md:w-auto">
                        Invia Messaggio
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* Map Section */}
        <section className="py-16 bg-muted/50">
          <div className="container">
            <h2 className="text-3xl font-bold mb-8 text-center">Come Raggiungerci</h2>
            <Card className="overflow-hidden">
              <div className="aspect-video bg-muted flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <MapPin className="h-12 w-12 mx-auto mb-4" />
                  <p>Mappa interattiva del campo di volo</p>
                  <p className="text-sm mt-2">Campo di Volo Bicianca, Monza (MB)</p>
                </div>
              </div>
            </Card>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
