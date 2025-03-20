### 16-02-25 Modular API Functions v 0.1.1

Here we set the start of the version counting.

v1.x.x - when both server and client works

v0.1.x - for client developing

v0.2.x - for server developing

v0.3.x - for comunication, requirements and edge cases developing

v0.1.1 - Modular API (not fully implemented)

Different versions of client and server should work together since the mayor version number still the same (e.g 1.1.3 and 1.2.3 should work together)

Este commit es anterior a cambiar el parametro de dato de la API cliente para hacerlo genérico.
Debo añadir checks en la recepcion de datos para comprobar:
 - Existen todos los campos necesarios y los campos no nulificables tienen un valor correcto.
 - Los datos de entrada están bien formateados.

Tras adaptar la function de envio y recepcion de datos a una mas generica.
 - Crear tests para las nuevas funciones de la API.
 - Añadir los endpoint necesarios para cubir las nuevas funciones.

### 16-02-25 APIResponse and Log

There is a new APIResponse class. API response sub classes now inherit from the super APIResponse to keep it tidy 
and organized in the different posible API cases. I will be adding new ones in the future when necessary.
Current APIResponse classes and inheritances:

    SuccessResponse(APIResponse)
    ProcessResponse(SuccessResponse)
    ProgramResponse(SuccessResponse)
    SystemInfoResponse(SuccessResponse)
    LogResponse(SuccessResponse)
    ErrorResponse(APIResponse)
    NotFoundResponse(ErrorResponse)
    ValidationErrorResponse(ErrorResponse)
    InternalErrorResponse(ErrorResponse)

PopUp and test endpoint works.
Writing the execute program endpoint. It needs an "execute" function that executes the Command class when called.
Also add another command to kill the process, and list the current processes.

### 26-02-25 Dynamic endpoints

There is a blueprint for dynamic endpoints. The system import the dynamic endpoints on the server start.

### 03-03-25 Endpoint loader and more endpoints

A dynamic endpoints loader added and more dynamic endpoints were added.

### 06-03-25 Adding endpoints
Added system informationg gathering on the configuration file and a get function to access the information.

### 07-03-25 Adding endpoints
System information gathering function checked and working.
Added distintion between simple and complex endpoints.
Load and access by __getitem__ function to system_info and configuration.

### 20-03-25 Recursive endpoint loader
Remake of the endpoint loader to be recursive and load all the endpoints in the folder 'api'.
The endpoint blueprint changed to the new methodology.
Added auth endpoint to the api (login and logout).
Changed the API Request Tester to use the 'api/tree' endpoint to get all the endpoints.

*TODO* Add built-in endpoints as dynamic endpoints.

*TODO* Add the command shutdown, download from url, get screenshot, start program, get system information.