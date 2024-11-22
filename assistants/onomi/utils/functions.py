import logging
from .APIs import call_api_with_auth

def handle_required_action(client, run, thread_id, company, employee_number):
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    # print(f"TOOLS TO CALL:{tools_to_call}")
    logging.info(f"%s|%s| TOOLS TO CALL: {tools_to_call}",employee_number,company)
    # Available function, this function are define in the assistant
    available_function = ["get_current_employee_information","get_all_employees_information"]
    
    for tool in tools_to_call:
        function_name = tool.function.name
        # Check if function exists
        if function_name not in available_function:
            logging.warning(f"%s|%s| FUNCTION NAME: {function_name} NO FUNCTION DEFINE",employee_number,company)
            # Return response to the assistant
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{"tool_call_id": tool.id,"output": f"Function '{function_name}' is not defined in this assistant." }]
            )
            continue
        # print(f"FUNCTION NAME:{function_name}")
        logging.info(f"%s|%s| FUNCTION NAME: {function_name}",employee_number,company)
        params = tool.function.arguments
        # print(f"FUNCTION ARGS:{params}")
        logging.info(f"%s|%s| FUNCTION ARGS: {params}",employee_number,company)
        if function_name == "get_all_employees_information":
            # Execute API call
            response_data = get_plantilla_personal(company)
            if not response_data:
                response_data = "No data returned from the API."
            # print(f"API RESPONSE: {response_data}")
            logging.info(f"%s|%s| API RESPONSE: {response_data}",employee_number,company)
            # Return response to the assistant
            run = submit_tool_response(client, thread_id, run.id, tool.id, str(response_data))
        if function_name == "get_current_employee_information":
            # Execute API call
            response_data = get_info_empleado(company,employee_number)
            if not response_data:
                response_data = "No data returned from the API."
            # print(f"API RESPONSE: {response_data}")
            logging.info(f"%s|%s| API RESPONSE: {response_data}",employee_number,company)
            # Return response to the assistant 
            run = submit_tool_response(client, thread_id, run.id, tool.id, str(response_data))
    return run

def submit_tool_response(client, thread_id, run_id, tool_id, output):
    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=[{"tool_call_id": tool_id, "output": output}]
    )

def get_plantilla_personal(company):
    payload = {
        'company': int(company),
        'employeeType': '1',
        'bankData': '1',
        'personalData': '1'
    }
    response = call_api_with_auth("https://api.grupoono.lat/EeDetail", payload)
    return response

def get_info_empleado(company,employee_number):
    payload = {
        'company': int(company),
        'employeeType': '1',
        'bankData': '1',
        'personalData': '1',
        'EmployeeNumber':employee_number
    }
    response = call_api_with_auth("https://api.grupoono.lat/EeDetail", payload)
    return response
                