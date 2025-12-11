

interface Props {
    params: {
        id: string
    }
}

export default async function index({ params: { id } }: Props) {


    return <div>
        <h1>{id}</h1>
    </div>
}