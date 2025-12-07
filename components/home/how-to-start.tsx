import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Phone } from "lucide-react"

import people from "@/app/public/images/how-to-start.1.jpg"

export const HowToStart = () => (
    <section className="mx-4 bg-card">
        <div className="flex flex-col lg:flex-row gap-y-2 items-center">
            <div className="shadow-lg lg:basis-1/2">
                <img
                    src={people.src}
                    alt="Come iniziare"
                    className="w-full h-full object-cover max-h-[650px]"
                />
            </div>
            <div className="p-4 lg:basis-1/2">
                <h2 className="text-3xl md:text-4xl font-bold mb-6">Come Iniziare</h2>
                <p className="text-md leading-relaxed text-muted-foreground my-6">
                    Ogni anno il CAP per mezzo delle Associazioni locali organizza una serie di CORSI formativi per i costruttori o per coloro che vogliono toccare con mano le varie tecniche che coinvolgono la costruzione aeronautica. I corsi vengono tenuti da soci esperti costruttori e gli argomenti toccano tutti gli argomenti necessari per la buona riuscita di un progetto.
                </p>
                <p className="text-md leading-relaxed text-muted-foreground my-6">
                    La sede degli incontri può essere diversa in base all’associazione CAP che organizza lo stage teorico/pratico. La partecipazione ai corsi è gratuita per i soci CAP, per tutti gli altri viene richiesto un contributo variabile in funzione del materiale didattico messo a disposizione. Alle volte è prevista anche una convenzione con alberghi e ristoranti locali per vitto ed alloggio. Il numero massimo di partecipanti è sempre limitato ad una quindicina di persone per dar modo a tutti di prender parte attivamente alle esercitazioni in laboratorio.
                    I soci, o aspiranti tali, devono iscriversi direttamente a una delle otto Associazioni.
                </p>
                <div className="w-full flex justify-center">
                    <Button asChild size="lg" className="text-lg">
                        <Link href="/contatti">
                            Contatti
                            <Phone className="ml-2" />
                        </Link>
                    </Button>
                </div>
            </div>
        </div>
    </section>
)