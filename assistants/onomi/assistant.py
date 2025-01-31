# %%
import os
import sys
import time
import logging
from openai import OpenAI
from django.conf import settings
from assistants.onomi.models import QuestionToAnswer
from assistants.onomi.utils.functions import handle_required_action
from assistants.onomi.utils.messages import retrieve_annotation

#TODO:cambiar los errores de salida en la respuesta por una respuesta "Disculpe la molestia, por el momento la respuesta no esta disponible, favor de acercarse a su departamento de recursos humanos o intentar de nuevo mas tarde."

# Añadimos 'assistant' al root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
org_id = settings.OPENAI_ORG_ID
assistant_id = settings.OPENAI_ASSISTANT
log_file = settings.LOG_FILE

#Main function
def onomi_assistant(id_employee,company,question,database,thread_id,is_admin):
    # return format_response('hola','111','1','2','test','thread_ZtSrmPjhDLXzz7W8ljvoF5gj','0')
    # Set log
    logging.basicConfig(filename=log_file,format="%(levelname)s|%(asctime)s|%(message)s",level=logging.INFO)
    # Declare variables
    response = {}
    tokens_use = 0
    # Create instance of openAI client
    client = OpenAI(organization=org_id,api_key=api_key)
    # Define thread
    if not thread_id:
        # Create a thread
        thread = client.beta.threads.create(metadata={"user": id_employee,"company": company})
    else:
        # Retrieve a thread
        thread = client.beta.threads.update(thread_id,metadata={"modified": "true","user": id_employee,"company": company})
    logging.info(f"%s|%s| THREAD INFO: {thread}",id_employee,company)
    # Create a message and add it to the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        content=question,
        role="user",
        metadata={"user": id_employee,"company": company}
    )
    logging.info(f"%s|%s| MESSAGE INFO: {message}",id_employee,company)
    # Run the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        metadata={"user": id_employee,"company": company}
    )
    logging.info(f"%s|%s| RUN ID: {run.id}",id_employee,company)
    # Define max iterations for run control
    MAX_ITERATIONS = 75
    iteration_count = 0
    # Retrieve and Check status until completed
    while run.status not in ["completed", "failed", "cancelled", "incomplete", "expired"]:
        iteration_count += 1
        if iteration_count > MAX_ITERATIONS:
            run = client.beta.threads.runs.cancel(thread_id=thread.id,run_id=run.id)
            logging.error(f"%s|%s| Maximum iterations reached in RUN cycle. Exiting.", id_employee, company)
        # Verifiy running status 
        if run.status in ["queued", "in_progress", "cancelling"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
            logging.info(f"%s|%s| RUN STATUS: {run.status}",id_employee,company)
        # Handle the requires action
        elif run.status == "requires_action":
            logging.info(f"%s|%s| ENTER REQUIRED ACTION: {run.status}", id_employee, company)
            action_result = handle_required_action(client, run, thread.id, company, id_employee, is_admin)
            
            if isinstance(action_result, dict) and action_result.get("status") == "error":
                logging.error(f"%s|%s| ACTION FAILED: {action_result.get('message')}", id_employee, company)
                response.update({"assistant": action_result.get("message")})
                logging.error(f"%s|%s| TOKENS: {run}", id_employee, company)
                tokens_use = 0
                return format_response(question, id_employee, company, database, response, thread.id, tokens_use)
            else:
                run = action_result

    # Retrieve message when status is completed or failed
    if run.status == "completed":
        logging.info(f"%s|%s| RUN STATUS: {run.status}",id_employee,company)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        logging.info(f"%s|%s| MESSAGES: {messages}",id_employee,company)
        last_message = messages.data[0]
        response[last_message.role] = retrieve_annotation(client, thread.id, last_message.id)
        tokens_use = run.usage.total_tokens or 0
    elif run.status in ["failed", "cancelled", "incomplete", "expired"]:
        logging.info(f"%s|%s| RUN FAILED WITH STATUS: {run.status}", id_employee, company)
        logging.info(f"%s|%s| RUN DETAIL: {run}", id_employee, company)
        response.update({"assistant": "Sorry for the inconvenience. At the moment, the answer is not available. If you need immediate assistance, please contact your Human Resources department directly."})
        tokens_use = run.usage.total_tokens or 0
    else:
        logging.error(f"%s|%s| UNHANDLED RUN STATUS: {run.status}", id_employee, company)
        response.update({"assistant": "Sorry for the inconvenience. At the moment, the answer is not available. If you need immediate assistance, please contact your Human Resources department directly."})
        tokens_use = run.usage.total_tokens or 0
    
    logging.info(f"%s|%s| RUN USAGE: {tokens_use}",id_employee,company)
    # Return JSON response
    return format_response(question, id_employee, company, database, response, thread.id, tokens_use)

def format_response(question, id_employee, company, database, response, thread_id, tokens):
    json_response = QuestionToAnswer(
        question=question,
        id_employee=id_employee,
        compania=company,
        database=database,
        response=response,
        thread_id=thread_id,
        tokens=tokens
    )
    return json_response.to_json()