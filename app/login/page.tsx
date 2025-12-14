"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Lock, User } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
    const router = useRouter()
    const [loginData, setLoginData] = useState({
        username: "",
        password: "",
    })
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        if (!loginData.username || !loginData.password) {
            setError("Inserisci username e password")
            setLoading(false)
            return
        }

        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: loginData.username,
                    password: loginData.password,
                }),
            })

            if (!res.ok) {
                throw new Error("Credenziali non valide")
            }

            router.push("/area-soci")
            router.refresh()
        } catch (err) {
            setError("Login fallito. Controlla le tue credenziali.")
        } finally {
            setLoading(false)
        }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setLoginData((prev) => ({ ...prev, [name]: value }))
        setError("")
    }

    return (
        <div className="container flex items-center justify-center min-h-[calc(100vh-200px)] py-20">
            <Card className="w-full max-w-md">
                <CardContent className="p-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                            <Lock className="h-6 w-6 text-primary" />
                        </div>
                        <h2 className="text-2xl font-bold">Accedi</h2>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="username">Email</Label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                                <Input
                                    id="username"
                                    name="username"
                                    type="email"
                                    value={loginData.username}
                                    onChange={handleChange}
                                    placeholder="La tua email"
                                    className="pl-10"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                                <Input
                                    id="password"
                                    name="password"
                                    type="password"
                                    value={loginData.password}
                                    onChange={handleChange}
                                    placeholder="La tua password"
                                    className="pl-10"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                                <p className="text-sm text-destructive">{error}</p>
                            </div>
                        )}

                        <Button type="submit" size="lg" className="w-full" disabled={loading}>
                            {loading ? "Accesso in corso..." : "Accedi"}
                        </Button>

                        <div className="text-center">
                            <a href="#" className="text-sm text-primary hover:underline">
                                Password dimenticata?
                            </a>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
