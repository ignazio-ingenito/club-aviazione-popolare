import { Resend } from "resend"

const email_to = process.env.RESEND_EMAIL_TO || "ignazio.ingenito@gmail.com"
const email_from = process.env.RESEND_EMAIL_FROM || "noreply@skunklabs.uk"
const email_lang = process.env.RESEND_EMAIL_LANG || "it"

export async function POST(req: Request) {
    const apiKey = process.env.RESEND_API_KEY
    if (!apiKey) {
        return Response.json(
            { ok: false, error: "RESEND_API_KEY not set" },
            { status: 500 }
        )
    }

    const resend = new Resend(apiKey)
    const body = await req.json()
    const email = {
        from: `${email_from}`,
        to: `${email_to}`,
        replyTo: `${body.email}`,
        subject: `clubaviazionepopolare.org: ${email_to}`,
        headers: { "Content-Language": email_lang },
        html: `
            <html lang="${email_lang}">
            <body style="font-family: 'Open Sans', sans-serif; color:#333;">
                <table style="border-collapse: collapse;">
                    <tr>
                        <td style="padding: 0.5rem 0.25rem; border-top: solid 1px lightgray;">
                            <strong>Nome</strong>
                        </td>
                        <td style="padding: 0.5rem 0.25rem; border-top: solid 1px lightgray;">
                            ${body.name}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0.25rem;">
                            <strong>Email</strong>
                        </td>
                        <td style="padding: 0.5rem 0.25rem;">
                            ${body.email}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0.25rem;">
                            <strong>Telefono</strong>
                        </td>
                        <td style="padding: 0.5rem 0.25rem;">
                            ${body.phone}
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding: 0.5rem 0.25rem;">
                            <strong>Messaggio</strong>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding: 0.5rem 0.25rem; border-bottom: solid 1px lightgray">
                            ${body.message}
                        </td>
                    </tr>
                </table>
            </body>
            </html>
        `
    }

    try {
        const res = await resend.emails.send(email)
        console.info({
            route: `/api/mail`,
            method: `POST`,
            email: email,
            response: res
        })
        return Response.json({ ok: true })
    }
    catch (exception) {
        console.error({
            route: `/api/mail`,
            method: `POST`,
            email: email,
            error: exception,
        })
        return Response.json({ ok: false, error: exception })
    }

}
