"use client"

import { MapPin } from "lucide-react"
import { useState } from "react"

export default function MapContatti() {

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    subject: "",
    message: "",
  })


  return (
    <div className="text-center text-muted-foreground">
      <MapPin className="h-12 w-12 mx-auto mb-4" />
      <p>Mappa interattiva del campo di volo</p>
      <p className="text-sm mt-2">Campo di Volo Bicianca, Monza (MB)</p>
    </div>
  )
}
