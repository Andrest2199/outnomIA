from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from assistants.onomi.assistant import onomi_assistant

# Create your views here.
def index(request):
    return render(request,"index.html")

@csrf_exempt
def onomi(request):
    if request.method != "POST":
        return JsonResponse("Method not allowed", status=405, safe=False)

    try:
        req = json.loads(request.body.decode("utf-8"))
        id_employee = req.get("id_employee")
        compania = req.get("compania")
        question = req.get("question")
        database = req.get("database")
        thread_id = req.get("thread_id")
        # Validamos que haya un id empleado
        if not id_employee:
            return JsonResponse({"Error": "No Se Proporcionó Ningun ID de Empleado."}, status=400, safe=False)
        # Validamos que haya una pregunta
        if not question:
            return JsonResponse({"Error": "No Se Proporcionó Ninguna Pregunta."}, status=400, safe=False)
        # Validamos que haya una compania
        if not compania:
            return JsonResponse({"Error": "No Se Proporcionó Ninguna Compania."}, status=400, safe=False)
        # Validamos que haya una database
        if not database:
            return JsonResponse({"Error": "No Se Proporcionó Ninguna Base de Datos."}, status=400, safe=False)
        # Validamos el tipo de id empleado
        if type(id_employee) != str:
            return JsonResponse({"Error": "EL ID de Empleado debe ser enviado como cadena de texto."}, status=400, safe=False)
        # Validamos el tipo de question
        if type(question) != str:
            return JsonResponse({"Error": "La pregunta debe ser enviada como cadena de texto."}, status=400, safe=False)
        # Validamos el tipo de id empleado
        if type(compania) != str:
            return JsonResponse({"Error": "La compania debe ser enviada como cadena de texto."}, status=400, safe=False)
        # Validamos el tipo de id empleado
        if type(database) != str:
            return JsonResponse({"Error": "La base de datos debe ser enviada como cadena de texto."}, status=400, safe=False)
        # Validamos el tipo de thread_id
        if type(thread_id) != str and thread_id != '':
            return JsonResponse({"Error": "EL ID de Thread debe ser enviado como cadena de texto."}, status=400, safe=False)
        
        data = onomi_assistant(id_employee,compania,question,database,thread_id)
        # data= 'hola'
        return JsonResponse(data, status=200, safe=False)
    except ValueError as e:
        return JsonResponse({"Error": str(e)}, status=422)
    except Exception as e:
        return JsonResponse(str(e), status=500, safe=False)
