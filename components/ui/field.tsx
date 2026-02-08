import * as React from "react"

import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

function FieldSet({ className, ...props }: React.ComponentProps<"fieldset">) {
  return (
    <fieldset
      data-slot="field-set"
      className={cn("grid gap-6", className)}
      {...props}
    />
  )
}

function FieldGroup({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="field-group"
      className={cn("grid gap-6", className)}
      {...props}
    />
  )
}

type FieldProps = React.ComponentProps<"div"> & {
  "data-invalid"?: boolean
}

function Field({ className, "data-invalid": dataInvalid, ...props }: FieldProps) {
  return (
    <div
      data-slot="field"
      data-invalid={dataInvalid}
      className={cn("grid gap-2", className)}
      {...props}
    />
  )
}

function FieldLabel({
  className,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label
      data-slot="field-label"
      className={cn("data-[invalid=true]:text-destructive", className)}
      {...props}
    />
  )
}

function FieldDescription({
  className,
  ...props
}: React.ComponentProps<"p">) {
  return (
    <p
      data-slot="field-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
}

type FieldErrorProps = React.ComponentProps<"p"> & {
  errors?: Array<string | undefined> | string
}

function FieldError({ className, errors, ...props }: FieldErrorProps) {
  const list = (Array.isArray(errors) ? errors : [errors]).filter(Boolean) as string[]
  if (list.length === 0) {
    return null
  }

  return (
    <p
      data-slot="field-error"
      className={cn("text-sm text-destructive", className)}
      {...props}
    >
      {list.join(", ")}
    </p>
  )
}

export {
  FieldSet,
  FieldGroup,
  Field,
  FieldLabel,
  FieldDescription,
  FieldError,
}
