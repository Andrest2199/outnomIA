from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

# Create your views here.
@csrf_exempt
def onomi(request):
    if request.method != "POST":
        return JsonResponse("Method not allowed", status=405, safe=False)

    try:
        req = json.loads(request.body.decode("utf-8"))
        question = req.get("question")
        compania = req.get("compania")
        database = req.get("database")
        if question is None or question is '' or compania is None or compania is '' or database is None or database is '':
            return JsonResponse(
                f'Missing parameters compania or database, please verify.',
                status=400,
                safe=False,
            )
        data = {'compania':compania,'database':database}
        data2 = json.dumps(data)
        return JsonResponse(data2, status=200, safe=False)
    except ValueError as e:
        return JsonResponse({"Error": str(e)}, status=422)
    except Exception as e:
        return JsonResponse(str(e), status=500, safe=False)
