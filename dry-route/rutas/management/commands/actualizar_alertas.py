import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from rutas.alertas import RADIO_SIMULACION_M, UMBRAL_MM_POR_HORA, actualizar_puntos


def leer_lugar(texto):
    """'-33.4911,-70.6190' -> (-33.4911, -70.619)."""
    try:
        lat, lon = (float(parte) for parte in texto.split(","))
    except ValueError:
        raise CommandError("--cerca va como LAT,LON, sin espacios. Ejemplo: --cerca -33.4911,-70.6190") from None
    return lat, lon


class Command(BaseCommand):
    help = ("Consulta la lluvia en Open-Meteo y enciende o apaga solos los pasos bajo nivel (D14). "
            "Ejemplos: actualizar_alertas --cada 10 | actualizar_alertas --simular 10 --cerca -33.4911,-70.6190")

    def add_arguments(self, parser):
        parser.add_argument("--umbral", type=float, default=UMBRAL_MM_POR_HORA,
                            help=f"mm por hora desde los que se enciende un paso bajo nivel (por defecto {UMBRAL_MM_POR_HORA}, sin calibrar)")
        parser.add_argument("--simular", type=float, metavar="MM",
                            help="no consulta internet: hace como si lloviera MM mm por hora. Con 0 se termina la lluvia simulada")
        parser.add_argument("--cerca", metavar="LAT,LON",
                            help=f"con --simular, llueve solo a menos de {RADIO_SIMULACION_M} m de este lugar")
        parser.add_argument("--cada", type=float, metavar="MINUTOS",
                            help="repite la consulta cada MINUTOS minutos, hasta que se presione Ctrl + C")

    def handle(self, *args, **opciones):
        cerca = leer_lugar(opciones["cerca"]) if opciones["cerca"] else None
        if cerca and opciones["simular"] is None:
            raise CommandError("--cerca solo sirve junto con --simular: la lluvia real llega para toda la zona.")

        try:
            while True:
                self.actualizar_una_vez(opciones["umbral"], opciones["simular"], cerca)
                if not opciones["cada"]:
                    break
                time.sleep(opciones["cada"] * 60)
        except KeyboardInterrupt:
            self.stdout.write("Detenido. Los puntos quedan como estaban en la última actualización.")

    def actualizar_una_vez(self, umbral, simular, cerca):
        hora = timezone.localtime().strftime("%H:%M")
        resumen = actualizar_puntos(umbral, simular, cerca)
        if resumen is None:
            # No se cae: el comando sigue intentando en la próxima vuelta (con --cada)
            self.stderr.write(f"{hora} · No hubo datos de lluvia. Los puntos quedan como estaban.")
            return
        alerta = resumen["alerta"]
        estado = f"{alerta.get_nivel_display()}: {alerta.titulo}" if alerta else "Sin alertas de lluvia"
        self.stdout.write(self.style.SUCCESS(
            f"{hora} · Lluvia máxima ahora: {resumen['lluvia_max_mm']} mm/h "
            f"(próximas horas: {resumen['pronostico_max_mm']} mm/h). "
            f"Encendidos: {resumen['encendidos']}, apagados: {resumen['apagados']}. {estado}."
        ))
