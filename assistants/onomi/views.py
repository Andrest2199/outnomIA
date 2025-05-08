from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from assistants.onomi.assistant import onomi_assistant, transcribe
from assistants.onomi.utils.messages import retrieve_messages_thread
import json
import re


# Create your views here.
@csrf_exempt
def onomi(request):
    if request.method != "POST":
        return json_error("Method not allowed", 405)

    try:
        # Cargamos JSON
        req = json.loads(request.body.decode("utf-8"))

        id_employee = req.get("id_employee")
        database = req.get("database")
        compania = req.get("compania")
        question = req.get("question")
        thread_id = req.get("thread_id")
        is_admin = req.get("is_admin")
        # Validamos que haya un id empleado
        if not id_employee:
            return json_error("No Se Proporcionó Ningun ID de Empleado.")

        # Validamos que haya una pregunta
        if not question:
            return json_error("No Se Proporcionó Ninguna Pregunta.")

        # Validamos que haya una compania
        if not compania:
            return json_error("No Se Proporcionó Ninguna Compania.")

        # Validamos que haya una database
        if not database:
            return json_error("No Se Proporcionó Ninguna Base de Datos.")

        # Validamos el tipo de id empleado
        if type(id_employee) != str:
            return json_error(
                "EL ID de Empleado debe ser enviado como cadena de texto."
            )

        # Validamos el tipo de question
        if type(question) != str:
            return json_error("La pregunta debe ser enviada como cadena de texto.")

        # Validamos el tipo de id empleado
        if type(compania) != str:
            return json_error("La compania debe ser enviada como cadena de texto.")

        # Validamos el tipo de id empleado
        if type(database) != str:
            return json_error("La base de datos debe ser enviada como cadena de texto.")

        # Validamos el tipo de thread_id
        if type(thread_id) != str and thread_id != "":
            return json_error("EL ID de Thread debe ser enviado como cadena de texto.")

        data = onomi_assistant(
            id_employee, compania, question, database, thread_id, is_admin
        )

        return json_success(data)
    except ValueError as e:
        return json_error(e, 422)
    except Exception as e:
        return json_error(e, 500)


@csrf_exempt
def audio_transcribe(request):
    if request.method != "POST":
        return json_error("Method not allowed", 405)

    try:
        audio_file = request.FILES.get("audio")
        id_empleado = request.POST.get("empleado")
        compania = request.POST.get("compania")

        if not audio_file:
            return json_error("No se recibió archivo de audio.")

        # Extraer solo la subextensión (webm, wav, mpeg)
        match = re.match(r"^(audio|video)/([a-zA-Z0-9.+-]+)$", audio_file.content_type)

        if not match or match.group(2) not in ["webm", "wav", "mpeg", "ogg", "mp3"]:
            return json_error("Tipo de archivo no permitido.")

        if audio_file.size > 2 * 1024 * 1024:  # 2MB
            return json_error("Archivo demasiado grande. Máximo 2MB.")

        if not id_empleado or not compania:
            return json_error("Faltan parámetros obligatorios.")

        transcription = transcribe(id_empleado, compania, audio_file)

        if not (transcription):
            return json_error(
                "Ocurrio un error en la transcripción del audio, intente mas tarde.",
                422,
            )

        return json_success(transcription)

    except Exception as e:
        return json_error(e, 500)


@csrf_exempt
def retrieve_messages(request):
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    try:
        thread_id = request.GET.get("thread_id")
        # Validamos que haya un id empleado
        if not thread_id:
            return json_error("No Se Proporcionó Ningun Thread ID.")
        # Validamos el tipo de thread_id
        if not isinstance(thread_id, str):
            return json_error("EL ID de Thread debe ser enviado como cadena de texto.")

        data = retrieve_messages_thread(thread_id)

        if "error" in data.keys():
            return json_error(data.get("error"))

        return json_success(data)
    except ValueError as e:
        return json_error(e, 422)
    except Exception as e:
        return json_error(e, 500)


def json_success(data, status=200):
    return JsonResponse({"status": "success", "data": data}, status=status)


def json_error(message, status=400):
    return JsonResponse(
        {"status": "error", "error": {"message": message, "code": status}},
        status=status,
    )
