from .APIs import call_api_with_auth

def handle_required_action(client, run, thread_id, company, employee_number):
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    print(f"TOOLS TO CALL:{tools_to_call}")
    for tool in tools_to_call:
        function_name = tool.function.name
        print(f"FUNCTION NAME:{function_name}")
        params = tool.function.arguments
        print(f"FUNCTION ARGS:{params}")
        if function_name == "get_plantilla_empleados_compania":
            # Execute API call
            response_data = get_plantilla_personal(company)
            print(f"RESPONSE API: {response_data}")
            # Return response to the assistant
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{"tool_call_id": tool.id,"output": str(response_data) }]
            )
        if function_name == "get_informacion_empleado":
            # Execute API call
            response_data = get_info_empleado(company,employee_number)
            print(f"RESPONSE API: {response_data}")
            # Return response to the assistant 
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{"tool_call_id": tool.id,"output": str(response_data) }]
            )
    return run

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
                