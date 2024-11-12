# %%
import os
import sys
import time
import re
import requests
from openai import OpenAI
from assistants.onomi.models import QuestionToAnswer
from django.conf import settings

# Añadimos 'assistant' al root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
org_id = settings.OPENAI_ORG_ID
assistant_id = settings.OPENAI_ASSISTANT
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
            print(run.status)
        # Handle the requires action
        elif run.status == "requires_action":
            handle_required_action(client, run, thread.id)
    
    # Set error if run failed or option above and break cycle
    if run.status in ["failed", "cancelled", "incomplete", "expired"]:
        response.update({"Error": f"Run failed with status: {run.status}"})
        tokens_use = run.usage.total_tokens or 0
        return format_response(question, id_employee, company, database, response, thread.id, tokens_use)

    # Retrieve messages when status is completed
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages:
            citations = retrieve_annotation(client, thread.id, message.id)
            if len(citations) != 0:
                message.content[0].text.value += '\n' + '\n'.join(citations)
            response[message.role] = message.content[0].text.value
        tokens_use = run.usage.total_tokens
        print(f"RUN USAGE:{tokens_use}")

    # Devolver la respuesta en formato JSON
    return format_response(question, id_employee, company, database, response, thread.id, tokens_use)

def handle_required_action(client, run, thread_id):
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    print(f"TOOLS TO CALL:{tools_to_call}")
    for tool in tools_to_call:
        function_name = tool.function.name
        print(f"FUNCTION NAME:{function_name}")
        params = tool.function.arguments
        print(f"FUNCTION ARGS:{params}")
        if function_name == "get_plantilla_empleados_compania":
            # Ejecuta llamada a la API y envía la respuesta al asistente
            # AQUI LLAMAR A LA API LOS RESULTADOS DE VUELTOS SON EN UN JSON
            response_data = "Llamada a la API get_plantilla_empleados_compania"
            # url="api.localhost/EeDetail?EePage=10&p=1"
            # response_data = requests.post(url).json()
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{"tool_call_id": tool.id,"output": response_data }]
            )
        if function_name == "get_informacion_empleado":
            # Ejecuta llamada a la API y envía la respuesta al asistente
            response_data = "Llamada a la API get_informacion_empleado"
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{"tool_call_id": tool.id,"output": response_data }]
            )
# Disabled this function in production
def retrieve_annotation(client,thread_id,message_id):
    unique_citations = {}
    citations = []
    citation_index = 1
    # Retrieve the message object
    message = client.beta.threads.messages.retrieve(thread_id=thread_id,message_id=message_id)
    # Extract the message and the annotation
    message_content = message.content[0].text.value
    annotations = message.content[0].text.annotations
    print(f"annontations:{annotations}")
    # Iterate over the annotations and add footnotes
    for annotation in annotations:
        # Check if the annotation text already has a citation to avoid duplicates
        citation_text = annotation.text

        # Determine the source of the citation
        if (file_citation := getattr(annotation, 'file_citation', None)):
            print(f"file_citation:{file_citation}")
            file_id = file_citation.file_id
            try:
                cited_file = client.files.retrieve(file_id)
                filename = cited_file.filename
            except Exception as e:
                print(f"Error retrieving file {file_id}: {e}")
                filename = file_id
        elif (file_path := getattr(annotation, 'file_path', None)):
            print(f"filepath:{file_path}")
            file_id = file_path.file_id
            try:
                cited_file = client.files.retrieve(file_id)
                filename = cited_file.filename
            except Exception as e:
                print(f"Error retrieving file {file_id}: {e}")
                filename = file_id
        else:
            continue

        # Only add citation if it is unique
        if filename not in unique_citations:
            # Add to unique citations and append citation text with index
            unique_citations[filename] = citation_index
            citations.append(f'[{citation_index}] Retrieved from {filename}')
            citation_index += 1  # Increment the citation index for the next unique file
        # Replace annotation text in the message content with the correct index
        message_content = message_content.replace(citation_text, f' [{unique_citations[filename]}]')
        # Note: File download functionality not implemented above for brevity
    if citations:
        message_content += "\n\nReferences:\n" + "\n".join(citations)
    
    return message_content

def retrieve_messages_thread(thread_id):
    response = {}
    client = OpenAI(organization=org_id,api_key=api_key)
    try:
        thread = client.beta.threads.retrieve(thread_id)
        messages = client.beta.threads.messages.list(thread_id)
        for index, message in enumerate(messages):
            message.content[0].text.value = retrieve_annotation(client, thread.id, message.id)
            response[index] = {message.role: message.content[0].text.value}
    except Exception as e:
        return {"error": str(e)}
    return response

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