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
        return JsonResponse("Method not allowed", status=405, safe=False)

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
            return JsonResponse(
                "No Se Proporcionó Ningun ID de Empleado.",
                status=400,
                safe=False,
            )
        # Validamos que haya una pregunta
        if not question:
            return JsonResponse(
                "No Se Proporcionó Ninguna Pregunta.", status=400, safe=False
            )
        # Validamos que haya una compania
        if not compania:
            return JsonResponse(
                "No Se Proporcionó Ninguna Compania.", status=400, safe=False
            )
        # Validamos que haya una database
        if not database:
            return JsonResponse(
                "No Se Proporcionó Ninguna Base de Datos.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(id_employee) != str:
            return JsonResponse(
                "EL ID de Empleado debe ser enviado como cadena de texto.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de question
        if type(question) != str:
            return JsonResponse(
                "La pregunta debe ser enviada como cadena de texto.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(compania) != str:
            return JsonResponse(
                "La compania debe ser enviada como cadena de texto.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(database) != str:
            return JsonResponse(
                "La base de datos debe ser enviada como cadena de texto.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de thread_id
        if type(thread_id) != str and thread_id != "":
            return JsonResponse(
                "EL ID de Thread debe ser enviado como cadena de texto.",
                status=400,
                safe=False,
            )

        data = onomi_assistant(
            id_employee, compania, question, database, thread_id, is_admin
        )

        return JsonResponse(data, status=200, safe=False)
    except ValueError as e:
        return JsonResponse(str(e), status=422)
    except Exception as e:
        return JsonResponse(str(e), status=500, safe=False)


@csrf_exempt
def audio_transcribe(request):
    if request.method != "POST":
        return JsonResponse({"Error": "Method not allowed"}, status=405)

    try:
        audio_file = request.FILES.get("audio")
        id_empleado = request.POST.get("empleado")
        compania = request.POST.get("compania")

        if not audio_file:
            return JsonResponse(
                {"Error": "No se recibió archivo de audio."}, status=400
            )

        # Extraer solo la subextensión (webm, wav, mpeg)
        match = re.match(r"^(audio|video)/([a-zA-Z0-9.+-]+)$", audio_file.content_type)

        if not match or match.group(2) not in ["webm", "wav", "mpeg", "ogg", "mp3"]:
            return JsonResponse({"Error": "Tipo de archivo no permitido."}, status=400)

        if audio_file.size > 2 * 1024 * 1024:  # 2MB
            return JsonResponse(
                {"Error": "Archivo demasiado grande. Máximo 2MB."}, status=400
            )

        if not id_empleado or not compania:
            return JsonResponse(
                {"Error": "Faltan parámetros obligatorios."}, status=400
            )

        transcription = transcribe(id_empleado, compania, audio_file)

        if not (transcription):
            return JsonResponse(
                {
                    "Error": "Ocurrio un error en la transcripción del audio, intente mas tarde."
                },
                status=500,
            )

        return JsonResponse(transcription, status=200)

    except Exception as e:
        return JsonResponse({"Error": str(e)}, status=500)


@csrf_exempt
def retrieve_messages(request):
    if request.method != "GET":
        return JsonResponse("Method not allowed", status=405, safe=False)

    try:
        thread_id = request.GET.get("thread_id")
        # Validamos que haya un id empleado
        if not thread_id:
            return JsonResponse(
                "No Se Proporcionó Ningun ID de Hilo de Conversación.",
                status=400,
                safe=False,
            )
        # Validamos el tipo de thread_id
        if not isinstance(thread_id, str):
            return JsonResponse(
                "EL ID de Thread debe ser enviado como cadena de texto.",
                status=400,
                safe=False,
            )

        data = retrieve_messages_thread(thread_id)
        if "error" in data.keys():
            return JsonResponse(data.get("error"), status=404)

        return JsonResponse(data, status=200, safe=False)
    except ValueError as e:
        return JsonResponse(str(e), status=422)
    except Exception as e:
        return JsonResponse(str(e), status=500, safe=False)
