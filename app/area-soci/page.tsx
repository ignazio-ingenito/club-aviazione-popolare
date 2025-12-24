import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { Award, Calendar, FileText, Lock, Users } from "lucide-react"

import { me } from "@/lib/server"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default async function AreaSociPage() {
  const cookieStore = cookies()
  const token = cookieStore.get("access_token")?.value

  if (!token) {
    redirect("/login")
  }

  let user = null
  try {
    user = await me(token)
  } catch (e) {
    // Token might be invalid or expired
    redirect("/login")
  }

  return (
    <>
      {/* Hero Section */}
      <section className="relative py-20 bg-linear-to-br from-primary to-primary/80 text-primary-foreground">
        <div className="container">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-balance">Area Riservata Soci</h1>
          <p className="text-xl leading-relaxed max-w-3xl opacity-90">
            Benvenuto, {user?.first_name} {user?.last_name}. Qui puoi gestire la tua iscrizione e accedere ai documenti.
          </p>
        </div>
      </section>

      {/* Dashboard Section */}
      <section className="py-16 bg-background">
        <div className="container max-w-7xl">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* User Info Card */}
            <Card className="lg:col-span-1">
              <CardContent className="p-6">
                <div className="flex flex-col items-center text-center mb-6">
                  <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Users className="h-10 w-10 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">{user?.first_name} {user?.last_name}</h3>
                  <p className="text-muted-foreground">{user?.email}</p>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-muted-foreground">Ruolo</span>
                    <span className="font-medium">{user?.role?.name || "Socio"}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-muted-foreground">Stato</span>
                    <span className="font-medium capitalize">{user?.status || "Attivo"}</span>
                  </div>
                </div>
                <div className="mt-8">
                  <Button variant="outline" className="w-full">Modifica Profilo</Button>
                </div>
              </CardContent>
            </Card>

            {/* Content Area */}
            <div className="lg:col-span-2 space-y-8">
              <div>
                <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
                <p className="text-muted-foreground leading-relaxed mb-6">
                  Accedi a tutte le funzionalità riservate ai soci del club.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <FileText className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-1">Documenti</h3>
                      <p className="text-sm text-muted-foreground">
                        Statuto, regolamenti e verbali.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Calendar className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-1">Eventi</h3>
                      <p className="text-sm text-muted-foreground">
                        Calendario e iscrizioni eventi.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Users className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-1">Forum</h3>
                      <p className="text-sm text-muted-foreground">
                        Discussioni della community.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Award className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold mb-1">Iscrizione</h3>
                      <p className="text-sm text-muted-foreground">
                        Stato rinnovo e pagamenti.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
