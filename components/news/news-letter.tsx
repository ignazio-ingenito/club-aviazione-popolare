const Newsletter = () => (
    <section className="w-full flex justify-center my-6 py-14 bg-primary text-primary-foreground">
        <div className="max-w-4xl text-center">
            <h3 className="text-3xl font-bold mb-6">Resta Sempre Aggiornato</h3>
            <p className="text-lg leading-relaxed mb-8 opacity-90 max-w-xl">
                Iscriviti alla nostra newsletter per ricevere le ultime news, gli
                aggiornamenti e gli eventi e del CAP.
            </p>
            <div className="flex flex-col sm:flex-row gap-y-4 gap-x-1 justify-center max-w-md mx-auto">
                <input
                    type="email"
                    placeholder="Inserici la tua email..."
                    className="flex-1 px-4 py-3 rounded-l-lg text-foreground bg-background/90 focus:outline-none "
                />
                <button className="px-6 py-3 bg-orange-500 rounded-r-lg font-medium hover:bg-secondary/90 transition-colors">
                    Iscriviti
                </button>
            </div>
        </div>
    </section>
)

export default Newsletter