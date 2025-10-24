import { Mail, Phone } from "lucide-react"

type ContactsProps = {
    className?: string
    isScrolled: boolean
    phone?: string
    email?: string
    showText?: boolean
    textColor?: string
    scrolledTextColor?: string
    scrolledTextColorHover?: string
}

export function HeaderContacts({
    className,
    isScrolled,
    phone,
    email,
    showText = false,
    textColor,
    scrolledTextColor,
    scrolledTextColorHover
}: ContactsProps) {
    const phoneUrl = phone ? `tel:${phone.replace(/\s+/g, "")}` : undefined
    const emailUrl = email ? `mailto:${email}` : undefined
    const cssScrolled = isScrolled ? `${textColor}` : `${scrolledTextColor} hover:${scrolledTextColorHover}`
    return (
        <>
            {phoneUrl && (
                <a
                    href={phoneUrl}
                    className={`${className} ${cssScrolled}`}
                    aria-label={`Chiama ${phone}`}
                >
                    <Phone className="h-4 w-4" />
                    {showText && phone && (<span className="text-ellipsis overflow-x-hidden">{phone}</span>)}
                </a>
            )}
            {emailUrl && (
                <a
                    href={emailUrl}
                    className={`${className} ${cssScrolled}`}
                    aria-label={`Scrivi a ${email}`}
                >
                    <Mail className="h-4 w-4" />
                    {showText && email && (<span className="text-ellipsis overflow-x-hidden">{email}</span>)}
                </a>
            )}
        </>
    )
}