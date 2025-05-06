from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from assistants.onomi.assistant import onomi_assistant, transcribe
from assistants.onomi.utils.messages import retrieve_messages_thread
import json
import requests

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
                {"Error": "No Se Proporcionó Ningun ID de Empleado."},
                status=400,
                safe=False,
            )
        # Validamos que haya una pregunta
        if not question:
            return JsonResponse(
                {"Error": "No Se Proporcionó Ninguna Pregunta."}, status=400, safe=False
            )
        # Validamos que haya una compania
        if not compania:
            return JsonResponse(
                {"Error": "No Se Proporcionó Ninguna Compania."}, status=400, safe=False
            )
        # Validamos que haya una database
        if not database:
            return JsonResponse(
                {"Error": "No Se Proporcionó Ninguna Base de Datos."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(id_employee) != str:
            return JsonResponse(
                {"Error": "EL ID de Empleado debe ser enviado como cadena de texto."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de question
        if type(question) != str:
            return JsonResponse(
                {"Error": "La pregunta debe ser enviada como cadena de texto."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(compania) != str:
            return JsonResponse(
                {"Error": "La compania debe ser enviada como cadena de texto."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de id empleado
        if type(database) != str:
            return JsonResponse(
                {"Error": "La base de datos debe ser enviada como cadena de texto."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de thread_id
        if type(thread_id) != str and thread_id != "":
            return JsonResponse(
                {"Error": "EL ID de Thread debe ser enviado como cadena de texto."},
                status=400,
                safe=False,
            )

        data = onomi_assistant(
            id_employee, compania, question, database, thread_id, is_admin
        )
        # data = "hola"
        return JsonResponse(data, status=200, safe=False)
    except ValueError as e:
        return JsonResponse({"Error": str(e)}, status=422)
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

        if not audio_file.content_type in ["audio/webm", "audio/wav", "audio/mpeg"]:
            return JsonResponse({"Error": "Tipo de archivo no permitido."}, status=400)

        if audio_file.size > 20 * 1024 * 1024:  # 20MB
            return JsonResponse(
                {"Error": "Archivo demasiado grande. Máximo 20MB."}, status=400
            )

        if not id_empleado or not compania:
            return JsonResponse(
                {"Error": "Faltan parámetros obligatorios."}, status=400
            )

        transcription = transcribe(id_empleado, compania, audio_file)

        return JsonResponse({"status": "success", "data": transcription}, status=200)

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
                {"Error": "No Se Proporcionó Ningun ID de Hilo de Conversación."},
                status=400,
                safe=False,
            )
        # Validamos el tipo de thread_id
        if not isinstance(thread_id, str):
            return JsonResponse(
                {"Error": "EL ID de Thread debe ser enviado como cadena de texto."},
                status=400,
                safe=False,
            )

        data = retrieve_messages_thread(thread_id)
        if "error" in data.keys():
            return JsonResponse({"Error": data.get("error")}, status=404)

        return JsonResponse(
            {"message": "Success", "response": data}, status=200, safe=False
        )
    except ValueError as e:
        return JsonResponse({"Error": str(e)}, status=422)
    except Exception as e:
        return JsonResponse(str(e), status=500, safe=False)
