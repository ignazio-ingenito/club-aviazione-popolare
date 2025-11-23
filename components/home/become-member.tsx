import Link from "next/link"

import { Button } from '../ui/button'
import { UserPlus } from 'lucide-react'

import aircraft from "@/app/public/images/white-and-red-vintage-aircraft.jpg"


export const BecomeMember = () => (
    <section className="mx-4 mb-8 bg-primary text-primary-foreground">
        <div className="flex flex-col lg:flex-row-reverse gap-y-2 items-center">
            <div className="shadow-lg lg:basis-1/2">
                <img
                    src={aircraft.src}
                    alt="Aeromodello CAP"
                    className="w-full h-full object-cover"
                />
            </div>
            <div className='p-4 lg:basis-1/2'>
                <h2 className="text-3xl md:text-4xl font-bold mb-6 dark:text-foreground">Diventa uno di noi</h2>
                <p className="text-md leading-relaxed my-6 dark:text-accent-foreground">
                    I soci, o aspiranti tali, devono iscriversi direttamente a una delle associazioni locali.<br className="mb-1.5" />
                    Non è possibile iscriversi individualmente al sodalizio CAP, dato che lo stesso si occupa sopratutto dei rapporti delle proprie associazioni verso l’esterno (Autorità, Enti, altre associazioni sia in Italia che all’estero).
                </p>
                <div className="w-full flex justify-center">
                    <Button asChild size="lg" variant="secondary" className="text-lg text-accent">
                        <Link href="/contatti">
                            Come Iscriversi al CAP
                            <UserPlus className="ml-2" />
                        </Link>
                    </Button>
                </div>
            </div>
        </div>
    </section>
)
