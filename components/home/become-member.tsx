import Link from "next/link"
import Image from "next/image"

import { Button } from '../ui/button'
import { UserPlus } from 'lucide-react'

import aircraft from "@/app/public/images/become-member.jpg"


export const BecomeMember = () => (
    <section className="mx-4 bg-primary text-primary-foreground">
        <div className="flex flex-col lg:flex-row-reverse items-center">
            <div className="w-full shadow-lg lg:basis-1/2 lg:h-150">
                <Image
                    src={aircraft}
                    alt="Aeromodello CAP"
                    className="w-full lg:h-full object-cover"
                />
            </div>
            <div className='lg:basis-1/2 px-4'>
                <h2 className="text-3xl md:text-4xl font-bold mb-6 dark:text-foreground">Diventa uno di noi</h2>
                <p className="text-md leading-relaxed my-6 dark:text-accent-foreground">
                    I soci, o aspiranti tali, devono iscriversi direttamente a una delle associazioni locali.<br className="mb-1.5" />
                    Non è possibile iscriversi individualmente al sodalizio CAP, dato che lo stesso si occupa sopratutto dei rapporti delle proprie associazioni verso l’esterno (Autorità, Enti, altre associazioni sia in Italia che all’estero).
                </p>
                <div className="w-full flex justify-center pb-6 lg:pb-0">
                    <Button asChild size="lg" variant="secondary" className="text-lg text-accent">
                        <Link href="/contatti">
                            Come iscriversi
                            <UserPlus className="ml-2" />
                        </Link>
                    </Button>
                </div>
            </div>
        </div>
    </section>
)
