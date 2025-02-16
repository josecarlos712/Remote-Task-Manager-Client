16-02-25 Pre API Functions

Este commit es anterior a cambiar el parametro de dato de la API cliente para hacerlo genérico.
Debo añadir checks en la recepcion de datos para comprobar:
 - Existen todos los campos necesarios y los campos no nulificables tienen un valor correcto.
 - Los datos de entrada están bien formateados.

Tras adaptar la function de envio y recepcion de datos a una mas generica.
 - Crear tests para las nuevas funciones de la API.
 - Añadir los endpoint necesarios para cubir las nuevas funciones.