"use client"

import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"

enum MapType {
  Map,
  Satellite
}

export default function Map() {
  const [mapType, setMapType] = useState("map")


  return (
    <div className="w-full flex flex-col gap-y-1">
      <div className="flex items-center justify-end">

        <div className="w-40 text-right">
          <Select onValueChange={setMapType} defaultValue="map">
            <SelectTrigger>
              <SelectValue placeholder="Seleziona il tipo di mappa" />
            </SelectTrigger>
            <SelectContent position="popper">
              <SelectGroup defaultValue="map">
                <SelectLabel>Tipo mappa</SelectLabel>
                <SelectItem value="map">Mappa</SelectItem>
                <SelectItem value="sat">Satellite</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>
      <Card className="overflow-hidden">
        <div className="aspect-video flex items-center justify-center relative">
          {
            mapType == "map"
              ? <iframe width="100%" height="100%" src="https://maps.google.com/maps?hl=it&q=Club%20Aviazione%20Popolare&t=&z=18&ie=UTF8&iwloc=B&output=embed" />
              : <iframe width="100%" height="100%" src="https://maps.google.com/maps?hl=it&q=Club%20Aviazione%20Popolare&t=k&z=18&ie=UTF8&iwloc=B&output=embed" />
          }
        </div>
      </Card>
    </div>
  )
}
