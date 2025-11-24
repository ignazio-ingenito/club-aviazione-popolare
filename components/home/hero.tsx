import Link from "next/link"

import { Button } from "@/components/ui/button"

import { Calendar, Pencil } from "lucide-react"

import biplane from "@/app/public/images/biplane.jpg"

export const HomeHero = () => {
    return (
        <section className="relative h-[600px] flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-black/30 z-10" />
            <img
                src={biplane.src}
                alt="Aeromodello storico"
                className="absolute inset-0 w-full h-full object-none lg:object-cover pd-10"
            />
            <div className="container relative z-20 text-center text-white">
                <h1 className="text-5xl md:text-7xl font-bold mb-6 text-balance">Club Aviazione Popolare</h1>
                <p className="text-xl md:text-2xl mb-8 text-pretty max-w-3xl mx-auto leading-relaxed">
                    Sodalizio delle Associazioni Italiane di Costruttori di Aeromobili Amatoriali e Storici
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center px-4 sm:px-0">
                    <Button
                        asChild
                        size="lg"
                        variant="outline"
                        className="text-lg bg-accent/70 hover:bg-accent border-accent">
                        <Link href="/contatti">
                            Associarsi al CAP
                            <Pencil className="ml-2 h-5 w-5" />
                        </Link>
                    </Button>
                    <Button
                        asChild
                        size="lg"
                        variant="outline"
                        className="text-lg bg-white/10 hover:bg-white/20 text-white border-white/30"
                    >
                        <Link href="/eventi">
                            Scopri gli Eventi
                            <Calendar className="ml-2 h-5 w-5" />
                        </Link>
                    </Button>
                </div>
            </div>
        </section >
    )
}
