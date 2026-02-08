import Image from "next/image"
import { getFiles, getFolderBySlug } from "@/lib/server"

interface Props {
    slug: string
    exclude?: string[]
}

export default async function Gallery({ slug, exclude }: Props) {
    const { id } = await getFolderBySlug(slug)
    const files = id ? await getFiles(id) : []

    return (
        <section className="gallery">
            {files.filter(file => !exclude?.includes(file.id)).map(({ id, filename_download, title, width, height }) => (
                <a key={id} target="_blank"
                    href={`${process.env.DIRECTUS_PUBLIC_URL}/assets/${id}`}
                    title={title ?? filename_download}
                >
                    <Image
                        key={id}
                        src={`${process.env.DIRECTUS_PUBLIC_URL}/assets/${id}`}
                        alt={title ?? filename_download}
                        width={width ?? 650}
                        height={height ?? 650}
                        loading="lazy"
                    />
                </a>
            ))}
        </section>
    )
}