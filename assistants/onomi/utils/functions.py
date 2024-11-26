import logging
from .APIs import call_api_with_auth

def handle_required_action(client, run, thread_id, company, employee_number, is_admin=""):
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    logging.info(f"%s|%s| TOOLS TO CALL: {tools_to_call}",employee_number,company)
    # Available function, this function are define in the assistant
    available_function = ["get_current_session_employee_info","get_all_employees_information"]
    #Declare outputs response
    tool_outputs=[]
    for tool in tools_to_call:
        function_name = tool.function.name
        # Check if function exists
        if function_name not in available_function:
            logging.warning(f"%s|%s| FUNCTION NAME: {function_name} NO FUNCTION DEFINE",employee_number,company)
            # Response returned to the assistant
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": f"Function '{function_name}' is not defined in this assistant."
            })
            continue

        logging.info(f"%s|%s| FUNCTION NAME: {function_name}",employee_number,company)
        params = tool.function.arguments
        
        logging.info(f"%s|%s| FUNCTION ARGS: {params}",employee_number,company)
        logging.info(f"%s|%s| IS_ADMIN: {is_admin}",employee_number,company)
        if function_name == "get_all_employees_information" and is_admin:
            # Execute API call
            response_data = get_plantilla_personal(company)
            if not response_data:
                response_data = "No data returned from the API."
            
            logging.info(f"%s|%s| API RESPONSE: {response_data}",employee_number,company)
            # Response returned to the assistant
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": str(response_data)
            })
        elif function_name =="get_all_employees_information" and not is_admin:
            logging.info(f"%s|%s| API RESPONSE: The user doesn't have access to this information.",employee_number,company)
            # Response returned to the assistant
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": "The user doesn't have access to this information."
            })
            
        if function_name == "get_current_session_employee_info":
            # Execute API call
            response_data = get_info_empleado(company,employee_number)
            if not response_data:
                response_data = "No data returned from the API."
                
            logging.info(f"%s|%s| API RESPONSE: {response_data}",employee_number,company)
            # Response returned to the assistant
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": str(response_data)
            })
    # Check if there are outputs
    if tool_outputs:
        try:
            # Submit outputs to the assistant
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            logging.info(f"%s|%s| TOOL OUTPUTS SUBMITTED SUCCESSFULLY.", employee_number, company)
            return run
        except Exception as e:
            logging.error(f"%s|%s| FAILED TO SUBMIT TOOL OUTPUTS: {e}", employee_number, company)
            # Cancel the run explicitly
            try:
                run = client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run.id)
                logging.info(f"%s|%s| RUN CANCELLED DUE TO SUBMIT ERROR.", employee_number, company)
                return run
            except Exception as cancel_error:
                logging.error(f"%s|%s| FAILED TO CANCEL RUN: {cancel_error}", employee_number, company)
            # Return an error message to the main loop
            return {"status": "error", "message": "Sorry for the inconvenience. At the moment, the answer is not available. If you need immediate assistance, please contact your Human Resources department directly."}
    else:
        logging.error(f"%s|%s| NO TOOL OUTPUTS TO SUBMIT.", employee_number, company)
        # Cancel the run explicitly
        try:
            run = client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run.id)
            logging.info(f"%s|%s| RUN CANCELLED DUE TO NO TOOL OUTPUTS.", employee_number, company)
            return run
        except Exception as cancel_error:
            logging.error(f"%s|%s| FAILED TO CANCEL RUN: {cancel_error}", employee_number, company)
            # Return an error message to the main loop
            return {"status": "error", "message": "Sorry for the inconvenience. At the moment, the answer is not available. If you need immediate assistance, please contact your Human Resources department directly."}

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
                