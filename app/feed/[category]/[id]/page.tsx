
interface Props {
    params: {
        id: string
    }
}


export default async function index({ params }: Props) {
    const { id } = params

    return (
        <h1>{id}</h1>
    )
}