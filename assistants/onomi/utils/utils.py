from django.http import JsonResponse
import re
 
# Extrae el detalle del mensaje de Open AI
def extract_openai_error_details(error_str):
    try:
        code_match = re.search(r"Error code:\s*(\d+)", error_str)
        message_match = re.search(r"'message':\s*\"([^\"]+)\"", error_str)

        code = int(code_match.group(1)) if code_match else 400
        message = message_match.group(1) if message_match else str(error_str)

        return {"code": code, "message": message}
    except Exception as e:
        return str(error_str)


# Formatea la respuesta JSON success
def json_success(data, status=200):
    return JsonResponse({"status": "success", "data": data}, status=status)

# Formatea la respuesta JSON error
def json_error(message, status=400):
    return JsonResponse(
        {"status": "error", "error": {"message": message, "code": status}},
        status=status,
    )