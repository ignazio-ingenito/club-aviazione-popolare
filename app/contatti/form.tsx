"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"

const formSchema = z.object({
  name: z.string().trim().min(1, "Il nome è obbligatorio"),
  email: z.email("Inserisci un'email valida"),
  phone: z.string().trim().optional(),
  message: z
    .string()
    .trim()
    .min(1, "Il messaggio è obbligatorio")
    .min(10, "Il messaggio deve contenere almeno 10 caratteri"),
})

type FormValues = z.infer<typeof formSchema>

export default function FormContatti() {
  const [submitted, setSubmitted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      message: "",
    },
    mode: "onBlur",
  })

  const onSubmit = async (values: FormValues) => {
    setSubmitError(null)
    setSubmitted(false)

    try {
      const res = await fetch("/api/mail", {
        method: "POST",
        body: JSON.stringify(values),
        headers: { "Content-Type": "application/json" },
      })

      if (!res.ok) {
        throw new Error("Failed to send mail")
      }

      setSubmitted(true)
      form.reset()
      setTimeout(() => setSubmitted(false), 5000)
    } catch (_err) {
      setSubmitError("Invio non riuscito. Riprova tra qualche minuto.")
    }
  }

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = form

  return (
    <div className="form-contatti">
      {submitted && (
        <div className="mb-6 rounded-md border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <p className="text-green-800 dark:text-green-200">
            Grazie per averci contattato! Ti risponderemo al più presto.
          </p>
        </div>
      )}

      {submitError && (
        <div className="mb-6 rounded-md border border-destructive/40 bg-destructive/10 p-4">
          <p className="text-destructive">{submitError}</p>
        </div>
      )}

      <div className="form">
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="min-h-139.5 space-y-6 [&_input]:border-border/60 [&_input]:shadow-none [&_textarea]:border-border/60 [&_textarea]:shadow-none"
        >
          <FieldSet>
            <FieldGroup>
              <Field data-invalid={Boolean(errors.name)}>
                <FieldLabel htmlFor="name">
                  Nome <span className="text-destructive">*</span>
                </FieldLabel>
                <Input
                  id="name"
                  placeholder="Gianfranco Rotondi"
                  aria-invalid={Boolean(errors.name)}
                  aria-describedby={errors.name ? "name-error" : undefined}
                  {...register("name")}
                />
                <FieldError id="name-error" errors={errors.name?.message} />
              </Field>

              <Field data-invalid={Boolean(errors.email)}>
                <FieldLabel htmlFor="email">
                  Email <span className="text-destructive">*</span>
                </FieldLabel>
                <Input
                  id="email"
                  type="email"
                  placeholder="gianfranco.rotondi@me.com"
                  aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? "email-error" : undefined}
                  {...register("email")}
                />
                <FieldError id="email-error" errors={errors.email?.message} />
              </Field>

              <Field>
                <FieldLabel htmlFor="phone">Telefono (opzionale)</FieldLabel>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+39 1234567890"
                  {...register("phone")}
                />
              </Field>

              <Field data-invalid={Boolean(errors.message)}>
                <FieldLabel htmlFor="message">
                  Messaggio <span className="text-destructive">*</span>
                </FieldLabel>
                <Textarea
                  id="message"
                  rows={6}
                  placeholder="Scrivi qui il tuo messaggio..."
                  aria-invalid={Boolean(errors.message)}
                  aria-describedby={errors.message ? "message-error" : undefined}
                  {...register("message")}
                />
                <FieldError id="message-error" errors={errors.message?.message} />
              </Field>
            </FieldGroup>
          </FieldSet>

          <Button type="submit" size="lg" className="w-full md:w-auto" disabled={isSubmitting}>
            {isSubmitting ? "Invio in corso..." : "Invia Messaggio"}
          </Button>
        </form>
      </div>
    </div>
  )
}
