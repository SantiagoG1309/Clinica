# citas/emails.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, BadHeaderError

def enviar_recordatorio_correo(cita):
    try:
        asunto = f"Recordatorio de cita médica - {cita.fecha}"
        mensaje_html = render_to_string('citas/emails/recordatorio_cita.html', {
            'cita': cita,
        })
        mensaje_texto = strip_tags(mensaje_html)
        destinatario = cita.paciente.usuario.email

        send_mail(
            asunto,
            mensaje_texto,
            'pilarforero2006@gmail.com',
            [destinatario],
            html_message=mensaje_html,
        )
    except BadHeaderError:
        print("Error en el encabezado del correo.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")