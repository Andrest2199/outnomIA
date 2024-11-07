# %%
import os
import sys
from openai import OpenAI
import requests

from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Configura la clave de API de OpenAI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
api_key = settings.OPENAI_API_KEY
print(api_key)

#%%
def onomi_assistant(question, compania, database):
    # Declare variables
    assistant_instruction = ""
    # Define the instruction
    assistant_instruction = f"You are a helpful human resources assistant who knows about payroll laws and regulations for workers in Mexico City. You can understand and provide answers in English and Spanish. You will have some relevant information files about regulations, laws, rules and internal processes of the company, in addition, you will have information about the company's payroll so you can provide information to workers about their payroll or solve various doubts regarding human resources. Remember to keep according to the established parameters of knowledge if you do not know something or do not find something just answer 'Sorry for the inconvenience. At the moment the answer is not available. Please contact your Human Resources department directly. \n\n"
    # Set system role
    system_content = {"role": "system", "content": assistant_instruction}
    # Set user content
    user_content = {"role": "user", "content": question}
    # Create instance of openAI client
    client = OpenAI(api_key=api_key)