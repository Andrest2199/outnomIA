# %%
import os
import io
import sys
import time
import logging
from datetime import datetime
from openai import OpenAI
from django.conf import settings
from assistants.onomi.models import QuestionToAnswer
from assistants.onomi.utils.functions import handle_required_action
from assistants.onomi.utils.messages import retrieve_annotation
from assistants.onomi.utils.utils import extract_openai_error_details

# TODO:cambiar los errores de salida en la respuesta por una respuesta "Disculpe la molestia, por el momento la respuesta no esta disponible, favor de acercarse a su departamento de recursos humanos o intentar de nuevo mas tarde."

# Añadimos 'assistant' al root path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
org_id = settings.OPENAI_ORG_ID
assistant_id = settings.OPENAI_ASSISTANT
log_file = settings.LOG_FILE

# Set log
logging.basicConfig(
    filename=log_file,
    format="%(levelname)s|%(asctime)s|%(message)s",
    level=logging.INFO,
)


# Main function
def onomi_assistant(
    id_employee, company, question, database, thread_id, dataIAP, is_admin
):
    # Declare variables
    response = {}
    tokens_use = 0
    # Create instance of openAI client
    client = OpenAI(organization=org_id, api_key=api_key)
    # Define thread
    if not thread_id:
        # Create a thread
        thread = client.beta.threads.create(
            metadata={"user": id_employee, "company": company}
        )
    else:
        # Retrieve a thread
        thread = client.beta.threads.update(
            thread_id,
            metadata={"modified": "true", "user": id_employee, "company": company},
        )
    logging.info(f"%s|%s| THREAD INFO: {thread}", id_employee, company)
    # Create a message and add it to the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        content=question,
        role="user",
        metadata={"user": id_employee, "company": company},
    )
    logging.info(f"%s|%s| MESSAGE INFO: {message}", id_employee, company)
    # Definir las instrucciones adicionales para esta ejecución
    if dataIAP[3] == "agregar":
        additional_instructions = (
            f"Para este chat, el usuario te llamará '{dataIAP[0]}' y espera respuestas en '{dataIAP[1]}'.  La fecha actual es'{datetime.now()}'. "
            "Asegúrate de mantener este comportamiento durante toda la conversación."
        )
    else:
        additional_instructions = (
            f"Se ha actualizado tu personalización para este chat. Ahora tu nombre será '{dataIAP[0]}' "
            f"y responderás en '{dataIAP[1]}'. La fecha actual es'{datetime.now()}'. Asegúrate de usar este nuevo comportamiento desde ahora."
        )
    # Run the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        additional_instructions=additional_instructions,
        metadata={"user": id_employee, "company": company},
    )
    logging.info(f"%s|%s| RUN ID: {run.id}", id_employee, company)
    # Define max iterations for run control
    MAX_ITERATIONS = 75
    iteration_count = 0
    # Retrieve and Check status until completed
    while run.status not in [
        "completed",
        "failed",
        "cancelled",
        "incomplete",
        "expired",
    ]:
        iteration_count += 1
        if iteration_count > MAX_ITERATIONS:
            run = client.beta.threads.runs.cancel(thread_id=thread.id, run_id=run.id)
            logging.error(
                f"%s|%s| Maximum iterations reached in RUN cycle. Exiting.",
                id_employee,
                company,
            )
        # Verifiy running status
        if run.status in ["queued", "in_progress", "cancelling"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            logging.info(f"%s|%s| RUN STATUS: {run.status}", id_employee, company)
        # Handle the requires action
        elif run.status == "requires_action":
            logging.info(
                f"%s|%s| ENTER REQUIRED ACTION: {run.status}", id_employee, company
            )
            action_result = handle_required_action(
                client, run, thread.id, company, id_employee, is_admin
            )

            if (
                isinstance(action_result, dict)
                and action_result.get("status") == "error"
            ):
                logging.error(
                    f"%s|%s| ACTION FAILED: {action_result.get('message')}",
                    id_employee,
                    company,
                )
                response.update({"assistant": action_result.get("message")})
                logging.error(f"%s|%s| TOKENS: {run}", id_employee, company)
                tokens_use = 0
                return format_response(
                    question,
                    id_employee,
                    company,
                    database,
                    response,
                    thread.id,
                    tokens_use,
                )
            else:
                run = action_result

    # Retrieve message when status is completed or failed
    if run.status == "completed":
        logging.info(f"%s|%s| RUN STATUS: {run.status}", id_employee, company)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        logging.info(f"%s|%s| MESSAGES: {messages}", id_employee, company)

        # Filtrar solo mensajes del asistente generados por este run
        assistant_messages = [
            m for m in messages.data if m.role == "assistant" and m.run_id == run.id
        ]
        assistant_messages.sort(key=lambda m: m.created_at)

        # Unir respuestas completas con anotaciones
        full_response = "\n\n".join(
            retrieve_annotation(client, thread.id, msg.id) for msg in assistant_messages
        )

        response["assistant"] = full_response
        tokens_use = run.usage.total_tokens or 0
    elif run.status in ["failed", "cancelled", "incomplete", "expired"]:
        logging.info(
            f"%s|%s| RUN FAILED WITH STATUS: {run.status}", id_employee, company
        )
        logging.info(f"%s|%s| RUN DETAIL: {run}", id_employee, company)
        response.update(
            {
                "assistant": "Disculpe la molestia, por el momento la respuesta no esta disponible, favor de acercarse a su departamento de recursos humanos o intentar de nuevo mas tarde."
            }
        )
        tokens_use = run.usage.total_tokens or 0
    else:
        logging.error(
            f"%s|%s| UNHANDLED RUN STATUS: {run.status}", id_employee, company
        )
        response.update(
            {
                "assistant": "Disculpe la molestia, por el momento la respuesta no esta disponible, favor de acercarse a su departamento de recursos humanos o intentar de nuevo mas tarde."
            }
        )
        tokens_use = run.usage.total_tokens or 0

    logging.info(f"%s|%s| RUN USAGE: {tokens_use}", id_employee, company)
    # Return JSON response
    return format_response(
        question, id_employee, company, database, response, thread.id, tokens_use
    )


def transcribe(id_employee, company, audio):
    """
    Transcribe el audio a text usando whisper 1 de Open AI (auto deteccion de idioma).

    Parameters:
        audio (file-like): A Django `request.FILES['audio']` o un archivo abierto con `open(path, 'rb')`

    Returns:
        str: Texto transcrito o False
    """
    # TODO: Implementar validacion de audio vacio y transcripcion nula
    # Create instance of openAI client
    client = OpenAI(organization=org_id, api_key=api_key)
    try:
        logging.info(f"%s|%s| BEGIN TRANSCRIPTION: {audio}", id_employee, company)
        # Convertimos el InMemoryUploadedFile a BytesIO
        audio_bytes = io.BytesIO(audio.read())
        audio_bytes.name = audio.name  # Agregar nombre al archivo
        audio_bytes.seek(0)  # Asegurar que empieza desde el inicio

        # Llamada a la API Whisper
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_bytes, response_format="text"
        )
        logging.info(f"%s|%s| TRANSCRIPTION: {transcript}", id_employee, company)
        return transcript
    except Exception as e:
        logging.error(f"%s|%s| ERROR TRANSCRIPTION: {str(e)}", id_employee, company)
        details = extract_openai_error_details(str(e))
        return {"error": details["message"], "code": details["code"]}


def format_response(
    question, id_employee, company, database, response, thread_id, tokens
):
    json_response = QuestionToAnswer(
        question=question,
        id_employee=id_employee,
        compania=company,
        database=database,
        response=response,
        thread_id=thread_id,
        tokens=tokens,
    )
    return json_response.to_json()
