16-02-25 Pre API Functions

Este commit es anterior a cambiar el parametro de dato de la API cliente para hacerlo genérico.
Debo añadir checks en la recepcion de datos para comprobar:
 - Existen todos los campos necesarios y los campos no nulificables tienen un valor correcto.
 - Los datos de entrada están bien formateados.

Tras adaptar la function de envio y recepcion de datos a una mas generica.
 - Crear tests para las nuevas funciones de la API.
 - Añadir los endpoint necesarios para cubir las nuevas funciones.

16-02-25 APIResponse and Log

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

26-02-25 Dynamic endpoints
There is a blueprint for dynamic endpoints. The system import the dynamic endpoints on the server start.