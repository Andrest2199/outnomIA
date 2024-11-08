# %%
import os
import sys
import requests
# from assistants.onomi.models import QuestionToAnswer
from openai import OpenAI
from django.conf import settings

# Añadimos 'assistant' al root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
org_id = settings.OPENAI_ORG_ID

def onomi_assistant(id_employee,question,company,database,thread_id):
    # Declare variables
    response = {}
    # Create instance of openAI client
    client = OpenAI(organization=org_id,api_key=api_key)
    print(client)
    # Retrieve an assistant
    my_assistant = client.beta.assistants.retrieve("asst_JKcKNxvUA9Kv93swEiaXUmad")
    print(my_assistant)
    # Define thread
    if not thread_id:
        # Create a thread
        thread = client.beta.threads.create(
            metadata={
                "user": id_employee,
                "company": company
            })
    else:
        # Retrieve a thread
        thread = client.beta.threads.update(
            thread_id,
            metadata={
                "modified": "true",
                "user": id_employee,
                "company": company
            })
    print(f"THREAD INFO:{thread}")
    # Create a message and add it to the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        content=question,
        role="user",
        metadata={
            "user": id_employee,
            "company": company
        }
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
        assistant_id="asst_JKcKNxvUA9Kv93swEiaXUmad",
        metadata={
            "user": id_employee,
            "company": company
        }
    )
    print(f"RUN ID:{run.id}")
    # Retrieve the run data
    run = client.beta.threads.runs.retrieve(
        run_id=run.id,
        thread_id=thread.id,
    )
    print(f"RUN DATA:{run}")
    # Check Status
    run_status = run.status
    print(f"RUN STATUS:{run_status}")
    # Validate status
    if run_status == "requires_action":
        print(f"REQUIRES ACTION:{run_status}")
        tools_to_call = run.required_action.submit_tool_outputs.tool_calls
        print(f"NUMERO DE FUNCIONES A LLAMAR:{len(tools_to_call)}")
        print(f"FUNCIONES:{tools_to_call}")
        function_name = tools_to_call[0].function.name
        print(function_name)
        params = tools_to_call[0].function.arguments
        print(params)

        if function_name == "get_plantilla_personal":
            # Call the API
            response="Llamamos a la API"
            # Return the response to the run
            run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread.id,run_id=run.id,tool_outputs=response)

    # Check status until completed or options above
    while run.status not in ["completed","queued","requires_action"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
        print(run.status)
    # Retrieve messages when status is completed
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages:
            print(f"{message.role}|{message.content[0].text.value}")
        tokens_use = run.usage.total_tokens
    print(f"RUN USAGE:{tokens_use}")

#%%
onomi_assistant('Hola, soy nuevo en la empresa! Me llamo Andrés','',1,2)
    #%%
    json_response = QuestionToAnswer(
        question=question,
        compania=company,
        database=database,
        response='HOLA!',
        tokens=tokens_use
    )
    return json_response.to_json()