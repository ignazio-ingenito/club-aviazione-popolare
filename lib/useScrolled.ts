"use client"

import { useEffect, useLayoutEffect, useRef, useState } from "react"

type Options = {
    threshold?: number
    withResize?: boolean
}

export function useScrolled({ threshold = 10, withResize = true }: Options = {}) {
    const [isScrolled, setIsScrolled] = useState(false)
    const raf = useRef<number | null>(null)

    const readY = () =>
        Math.max(
            typeof window !== "undefined" ? window.scrollY : 0,
            typeof document !== "undefined" ? document.documentElement.scrollTop : 0
        )

    const update = () => setIsScrolled(readY() > threshold)

    // 1) Prima del paint: evita il flash al refresh con scroll ripristinato
    useLayoutEffect(() => {
        if (typeof window === "undefined") return
        update()
    }, [threshold])

    // 2) Eventi: scroll / (opz.) resize / load / pageshow (bfcache)
    useEffect(() => {
        if (typeof window === "undefined") return

        const onScrollOrResize = () => {
            if (raf.current) cancelAnimationFrame(raf.current)
            raf.current = requestAnimationFrame(update)
        }

        const onLoad = () => update()
        const onPageShow = (e: PageTransitionEvent) => {
            // Quando torni indietro col browser (bfcache) lo scroll è già giusto, aggiornalo subito
            if (e.persisted) update()
        }

        window.addEventListener("scroll", onScrollOrResize, { passive: true })
        if (withResize) window.addEventListener("resize", onScrollOrResize)
        window.addEventListener("load", onLoad)
        window.addEventListener("pageshow", onPageShow as EventListener)

        // micro-poll per Safari/iOS che a volte setta lo scroll dopo il load
        let frame = 0
        const kick = () => {
            if (frame++ < 3) raf.current = requestAnimationFrame(kick)
            update()
        }
        raf.current = requestAnimationFrame(kick)

        return () => {
            window.removeEventListener("scroll", onScrollOrResize)
            if (withResize) window.removeEventListener("resize", onScrollOrResize)
            window.removeEventListener("load", onLoad)
            window.removeEventListener("pageshow", onPageShow as EventListener)
            if (raf.current) cancelAnimationFrame(raf.current)
        }
    }, [threshold, withResize])

    return isScrolled
}