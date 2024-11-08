# %%
import os
import sys
import time
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
    # return format_response(question,id_employee,company,database,'Hola, soy un asistente de recursos humanos! \n\n Estoy aquí para ayudarte con consultas relacionadas con nómina, leyes y regulaciones laborales en México. Puedo proporcionarte información sobre procesos internos de la empresa, así como responder preguntas sobre tu situación laboral. Si tienes alguna pregunta específica, no dudes en decírmelo.',1266)
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
    # # Retrieve a message
    # message = client.beta.threads.messages.retrieve(
    #     message_id="msg_abc123",
    #     thread_id="thread_abc123",
    # )
    # print(message)
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
        return format_response(question, id_employee, company, database, response, tokens_use)

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
    return format_response(question, id_employee, company, database, response, tokens_use)

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
            response_data = "Llamada a la API get_plantilla_empleados_compania"
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

def retrieve_annotation(client,thread_id,message_id):
    # Retrieve the message object
    message = client.beta.threads.messages.retrieve(thread_id=thread_id,message_id=message_id)
    print(message)
    # Extract the message and the annotation
    message_content = message.content[0].text.value
    annotations = message.content[0].text.annotations
    citations = []
    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content = message_content.replace(annotation.text, f' [{index + 1}]')
        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f'[{index + 1}] Retrieved from {cited_file.filename}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            cited_file = client.files.retrieve(file_path.file_id)
            citations.append(f'[{index + 1}] Click <here> to download {cited_file.filename}')
            # Note: File download functionality not implemented above for brevity
    return citations

def format_response(question, id_employee, company, database, response, tokens):
    json_response = QuestionToAnswer(
        question=question,
        id_employee=id_employee,
        compania=company,
        database=database,
        response=response,
        tokens=tokens
    )
    return json_response.to_json()