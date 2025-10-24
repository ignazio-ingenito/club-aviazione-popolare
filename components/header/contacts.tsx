import { Mail, Phone } from "lucide-react"

type ContactsProps = {
    css?: string
    isScrolled: boolean
    phone?: string
    email?: string
}

export function HeaderContacts({ css = "", isScrolled, phone, email, }: ContactsProps) {
    const telHref = phone ? `tel:${phone.replace(/\s+/g, "")}` : undefined
    const mailHref = email ? `mailto:${email}` : undefined

    return (
        <div className={`${css}`}>
            {telHref && (
                <a
                    href={telHref}
                    className={
                        `${isScrolled ? "text-accent" : "text-white hover:text-accent"} flex items-center gap-1 hover:scale-110 transition-all`
                    }
                    aria-label={`Chiama ${phone}`}
                >
                    <Phone className="h-4 w-4" />
                </a>
            )}
            {
                mailHref && (
                    <a
                        href={mailHref}
                        className={`${isScrolled ? "text-accent" : "text-white hover:text-accent"
                            } flex items-center gap-1 hover:scale-110 transition-all`}
                        aria-label={`Scrivi a ${email}`}
                    >
                        <Mail className="h-4 w-4" />
                    </a>
                )
            }
        </div >
    )
}