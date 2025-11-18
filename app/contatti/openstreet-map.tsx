"use client"

import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
const OpenStreetMap = () => {
    const mapRef = useRef<HTMLDivElement | null>(null)
    const coordinates: L.LatLngExpression = [45.541457, 9.19622]
    const iconUrl = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48ZyBmaWxsPSJub25lIj48cGF0aCBmaWxsPSIjZTNlM2UzIiBkPSJNMjAuODAzIDkuODFhOC44MDEgOC44MDEgMCAxIDAtMTMuMTk0IDcuNjE4YzEuNjUuOTUyIDIuMDk1IDIuMDA0IDMuOTY3IDUuMzIzYS40OS40OSAwIDAgMCAuODUyIDBjMS44OTEtMy4zNTYgMi4zMi00LjM3MyAzLjk2Ni01LjMyM2E4Ljc4IDguNzggMCAwIDAgNC40MDktNy42MTgiLz48cGF0aCBmaWxsPSIjZmZmIiBkPSJNMTIgMS4wMDlhOC43OTUgOC43OTUgMCAwIDAtNC4zOTIgMTYuNDE5YzEuNjUuOTUyIDIuMDk1IDIuMDA0IDMuOTY3IDUuMzIzYS40OS40OSAwIDAgMCAuNDI2LjI0OXoiLz48cGF0aCBzdHJva2U9IiMxOTE5MTkiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgZD0iTTIwLjgwMyA5LjgxYTguODAxIDguODAxIDAgMSAwLTEzLjE5NCA3LjYxOGMxLjY1Ljk1MiAyLjA5NSAyLjAwNCAzLjk2NyA1LjMyM2EuNDkuNDkgMCAwIDAgLjg1MiAwYzEuODkxLTMuMzU2IDIuMzItNC4zNzMgMy45NjYtNS4zMjNhOC43OCA4Ljc4IDAgMCAwIDQuNDA5LTcuNjE4IiBzdHJva2Utd2lkdGg9IjEiLz48cGF0aCBmaWxsPSIjZmZlZjVlIiBzdHJva2U9IiMxOTE5MTkiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgZD0iTTE3LjIyIDYuNjA0YTEuMzUgMS4zNSAwIDAgMSAuNDIxIDIuNDU1bC03LjY3OCA0Ljc2OGEuNDcuNDcgMCAwIDEtLjUyMi0uMDE0bC0yLjgxOC0xLjk3N2EuMjYuMjYgMCAwIDEgLjAwNC0uNDFsMS4xODItMS4wNDFhLjI2LjI2IDAgMCAxIC4yNS0uMDQzbDEuNDgxLjg4bDEuODc4LTEuMzFsLTMuNTU0LTIuMmEuMzIzLjMyMyAwIDAgMSAuMDE1LS41MDZsLjg3LS42NDVhLjMyLjMyIDAgMCAxIC4zMDUtLjA0M2w0LjkwMyAxLjgyNWwyLjI3LTEuNTQ4YTEuMjYgMS4yNiAwIDAgMSAuOTk0LS4xOSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9nPjwvc3ZnPg=="

    useEffect(() => {
        if (!mapRef.current)
            return

        const mapInstance = L.map(mapRef.current, {
            center: coordinates,
            zoom: 16,
        })

        // OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap',
        }).addTo(mapInstance)

        const icon = new L.Icon({
            iconUrl: iconUrl,
            iconSize: [40, 40],  // Size of the icon
            iconAnchor: [20, 40],  // Anchor point (where the tip of the pin points)
            popupAnchor: [0, -40],  // Popup position relative to the icon
        })
        L.marker(coordinates, { icon }).addTo(mapInstance)
            .bindPopup(`
                <p style="font-family: 'Open Sans', sans-serif; font-size: 19px;">
                    <b style="color: #50565a;">Club Aviazione Popolare</b><br />
                    <span style="font-size: 17px; line-height: 1.25rem;">Via Piave, 36</span><br />
                    <span style="font-size: 16px; line-height: 1.25rem;">20091 – Bresso (Mi)</span><br />
                    <span style="font-size: 16px; line-height: 1.25rem;">+39 02 6107142</span>
                </p>
            `)
        // .openPopup()

        return () => {
            mapInstance.remove()
        }
    }, [])

    return (
        <div ref={mapRef} className="aspect-video flex justify-center items-center"></div>
    )
}

export default OpenStreetMap
