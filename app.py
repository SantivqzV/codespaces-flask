# Importar librerías de flask y twilio
from flask import Flask, render_template, request
import mysql.connector
import matplotlib.pyplot as plt
from io import BytesIO
from twilio.rest import Client
import base64

# Asignar las claves para las variables de autenticación
account_sid = 'AC61af772734d5e9e9d0e8a2373851e370'
auth_token = 'ab66843181e465714d16191a7a9dfc8d'
client = Client(account_sid, auth_token)

app = Flask(__name__)

# Función que crea una conexión con la base de datos utilizando la librería de mysql.connector
def createConnection(user_name, database_name, user_password, host, port):
    cnx = mysql.connector.connect(
        user=user_name, database=database_name, password=user_password, host=host, port=port)
    cursor = cnx.cursor()
    return (cnx, cursor)

tempMessageEncendido=False
humMessageEncendido=False
humyTempEncendido=False

#Solamente solo se reciben datos del emulador virtual (clase Martes 16 de Enero)
@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    global tempMessageEncendido
    global humMessageEncendido
    global humyTempEncendido
    
    if request.headers['Content-Type'] == 'application/json':
        data = request.json

        # Se asignan los valores obtenidos de wokwi a sus variables correspondientes de codespaces
        humedad = str(data.get('humidity'))
        temperatura = str(data.get('temperature'))
        movimiento = str(data.get('movement'))
        tiempo = str(data.get('tiempo'))
        
        print(temperatura)
        print(humedad)
        print(movimiento)
        print(tiempo)

        #Se crea una conexión a la base de datos previamente establecida. 
        #DB name, User Name, pwd, host, port
        cnx, cursor = createConnection('sql5680674', 'sql5680674', 'jb8y5WbCJ6', 'sql5.freemysqlhosting.net', '3306')

        # Se utiliza un función de inserción de sql para insertar los datos a su tabla correspondiente en la base de datos
        add_data = ("INSERT INTO INFO (temperatura, humedad, movimiento, tiempo) VALUES ("+temperatura+","+humedad+","+movimiento+",'"+tiempo+"')")
        
        # Se ejecuta la función add_data
        cursor.execute(add_data)

        # Se guardan los cambios
        cnx.commit()

        # Se cierra esta instancia del proceso. 
        cursor.close()
        cnx.close()
        
        
        #Enciende dispositivos
        if float(humedad) > 55 and float(temperatura) > 30 and not humyTempEncendido: #Este caso es donde ambos son altos
            message = client.messages.create(
            from_='whatsapp:+14155238886',
            body='Humedad: '+humedad+"\nTemperatura:"+temperatura+'\n\nEncendiendo deshumidificador y ventilador',
            to='whatsapp:+5218117787532'
            )
            print(message.sid)
            humyTempEncendido=True
            humMessageEncendido=True
            tempMessageEncendido=True
        else:
            if float(humedad) > 55 and not humMessageEncendido: 
                message = client.messages.create(
                from_='whatsapp:+14155238886',
                body='Humedad: '+humedad+'\nEncendiendo el deshimudificador',
                to='whatsapp:+5218117787532'
                )
                print(message.sid)
                humMessageEncendido=True

            if float(temperatura) > 30 and not tempMessageEncendido:
                message = client.messages.create(
                from_='whatsapp:+14155238886',
                body='Temperatura: '+temperatura+'\nEncendiendo el ventilador',
                to='whatsapp:+5218117787532'
                )
                print(message.sid)
                tempMessageEncendido=True

        #Apaga dispositivos
        if float(humedad) <= 25 and float(temperatura) <= 22 and humyTempEncendido:
            message = client.messages.create(
            from_='whatsapp:+14155238886',
            body='Humedad: '+humedad+"\nTemperatura:"+temperatura+'\n\nApagando deshumidificador y ventilador',
            to='whatsapp:+5218117787532'
            )
            print(message.sid)
            humyTempEncendido=False
            humMessageEncendido=False
            tempMessageEncendido=False
        else:
            if float(humedad) <= 25 and humMessageEncendido:
                message = client.messages.create(
                from_='whatsapp:+14155238886',
                body='Humedad: '+humedad+'\nApagando el deshimudificador',
                to='whatsapp:+5218117787532'
                )
                print(message.sid)
                humMessageEncendido=False

            if float(temperatura) <= 22 and tempMessageEncendido:
                message = client.messages.create(
                from_='whatsapp:+14155238886',
                body='Temperatura: '+temperatura+'\nApagando el ventilador',
                to='whatsapp:+5218117787532'
                )
                print(message.sid)
                tempMessageEncendido=False
        
        return 'Data received successfully.', 200
    else:
        return 'Invalid content type. Expected application/json.', 0

#Mostramos la pagina web, al cargarse la página se manda un mensaje automáticamente 
@app.route("/", methods=['GET'])
def hello_world():
    # Create a connection to the database
    cnx, cursor = createConnection('sql5680674', 'sql5680674', 'jb8y5WbCJ6', 'sql5.freemysqlhosting.net', '3306')

    # Query the database
    query = ("SELECT * FROM INFO")

    # Execute the query
    cursor.execute(query)

    # Get the data
    data = cursor.fetchall()

    # Close the connection
    cursor.close()
    cnx.close()

    # Obtener los valores de x e y desde los datos
    x = [item[0] for item in data]
    y1 = [item[1] for item in data]
    y2 = [item[2] for item in data]
    y3 = [item[3] for item in data]

    # Crear la gráfica
    plt.figure(figsize=(8, 4))
    plt.plot(x, y1, label='Temperatura')
    plt.plot(x, y2, label='Humedad')
    plt.plot(x, y3, label='Movimiento')
    plt.legend()
    plt.title("DATOS A TRAVES DEL TIEMPO")

    # Guardar la gráfica en un archivo temporal
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode()

    # Renderizar la plantilla HTML con la gráfica
    return render_template('graph.html', img_data=img_data)
