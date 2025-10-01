"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-9 w-9">
        <Sun className="h-5 w-5" />
      </Button>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      aria-label="Cambia tema"
      aria-pressed={theme === 'dark'}
      className={`flex items-center gap-1 hover:text-accent transition-all duration-300 hover:scale-125 hover:cursor-pointer ${className}`}
    >
      <span className="relative inline-block size-5">
        <Sun
          className={[
            "absolute inset-0 size-5 transition-all duration-300",
            theme === "light"
              ? "rotate-90 scale-0 opacity-0"
              : "rotate-0 scale-100 opacity-100"
          ].join(" ")}
        />
        <Moon
          className={[
            "absolute inset-0 size-5 transition-all duration-300",
            theme === "light"
              ? "rotate-0 scale-100 opacity-100"
              : "-rotate-90 scale-0 opacity-0"
          ].join(" ")}
        />
      </span>
      <span className="sr-only">Cambia tema</span>
    </button>
  )
}
