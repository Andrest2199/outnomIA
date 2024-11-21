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

logging.basicConfig(level=logging.INFO)

#TODO:logging.info(f"THREAD INFO: {thread}")
#TODO:logging.error(f"Error retrieving file {file_id}: {e}")

# Añadimos 'assistant' al root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
org_id = settings.OPENAI_ORG_ID
assistant_id = settings.OPENAI_ASSISTANT

#Main function
def onomi_assistant(id_employee,company,question,database,thread_id):
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
    print(f"THREAD INFO:{thread}")
    # Create a message and add it to the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        content=question,
        role="user",
        metadata={"user": id_employee,"company": company}
    )
    print(f"MESSAGE ID:{message}")
    # Run the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        metadata={"user": id_employee,"company": company}
    )
    print(f"RUN ID:{run.id}")
    # Retrieve and Check status until completed
    while run.status not in ["completed", "failed", "cancelled", "incomplete", "expired"]:
        # Verifiy running status 
        if run.status in ["queued", "in_progress", "cancelling"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
            print(f"RUN STATUS:{run.status}")
        # Handle the requires action
        elif run.status == "requires_action":
            print(f"RUN STATUS ENTER REQUIRED ACTION:{run.status}")
            run = handle_required_action(client, run, thread.id, company, id_employee)
    
        # Set error if run failed or option above and break cycle
        elif run.status in ["failed", "cancelled", "incomplete", "expired"]:
            print(f"Run failed with status: {run.status} and {run}")
            response.update({"Error": f"Run failed with status: {run.status}"})
            tokens_use = run.usage.total_tokens or 0
            return format_response(question, id_employee, company, database, response, thread.id, tokens_use)

    # Retrieve message when status is completed
    if run.status == "completed":
        print(f"RUN STATUS:{run.status}")
        index = 0
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        print(f"MESSAGES:{messages}")
        last_message = messages.data[0]
        response[last_message.role] = retrieve_annotation(client, thread.id, last_message.id)
        tokens_use = run.usage.total_tokens or 0
        print(f"RUN USAGE:{tokens_use}")

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