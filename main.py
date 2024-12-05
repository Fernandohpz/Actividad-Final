from lib.bmp280 import BMP280
import lib.ssd1306
import network
import machine
from machine import I2C, Pin, SoftI2C
from lib.mqtt.simple import MQTTClient
import time

#INICIALIZACION DE PANTALLA
bus = SoftI2C(scl=Pin(5), sda=Pin(4))
oled_width = 128
oled_height = 64
oled = lib.ssd1306.SSD1306_I2C(oled_width, oled_height, bus)
devices = bus.scan()
if devices:
    print('Pantalla encontrada en la direccion', devices)
    oled.text("INICIANDO...", 20, 30)
    oled.show()
    time.sleep(3)
else:
    print('No se encontraron dispositivos I2C')


#SENSOR DE CALIDAD DE AIRE
anapin=machine.ADC(28)

#INICIALIZACION DEL SENSOR HUMEDAD Y TEMPERATURA
i2c = I2C(0, scl=Pin(1), sda=Pin(0),freq=40000)  
bmp = BMP280(i2c)
bmp.normal_measure()

devices = i2c.scan()
if devices:
    print('Sensor encontrado en las direccion', devices)
    oled.fill(0)
    oled.text("SENSORES LISTOS", 0, 30)
    oled.show()
    time.sleep(3)
else:
    print('No se encontraron dispositivos I2C')


#CONEXION A INTERNET
wlan=network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)
wlan.connect("","")#SSID,CONTRASEÑA

#VALIDACION DE CONEXION
while not wlan.isconnected():
    print('Error al conectarse REINTENTANDO')
    oled.fill(0)
    oled.text("CONECTANDO...", 20, 30)
    oled.show()
#    time.sleep(3)
    pass
print('Conectado a Wi-Fi:', wlan.ifconfig())


#CREDENCIALES PARA CONEXION CON EL SERVIDOR
idcliente = b"" #ID DISPOSITIVO
user = b"" #ID DISPOSITIVO
passw = b"" #CONTRASEÑA DEL DISPOSITIVO
canalid = b'' #API KEY WRITE


#USO DE CREDENCIALES PARA MQTT CLIENT
client = MQTTClient(server=b"mqtt3.thingspeak.com",
                    client_id=idcliente, 
                    user=user, 
                    password=passw, 
                    ssl=False)


#CONEXION CON THINGSPEAK
client.connect()


#CICLO PRINCIPAL
while True:

#DEFINICION DE VARIABLES PARA DATOS
    oled.fill(0)
    temp_pantalla = bmp.temperature
    pres_pantalla = round(bmp.pressure)
    sensor_aire=anapin.read_u16()

#IMPRESION DE LOS DATOS EN PANTALLA
    print("*******************************************")
    print("Temperatura: {:.2f} C".format(temp_pantalla))
    print("Presion: {:.2f} hPa".format(pres_pantalla))
    print("prescencia de gases valor: ", sensor_aire )

#VALORES EN LA OLED
    oled.text('Temperatura:', 0, 0)
    oled.text("{:.2f} C".format(temp_pantalla), 30, 10)
    oled.text('Presion:', 0, 20)
    oled.text("{:.2f} hpa".format(pres_pantalla), 20, 30)
    oled.text('Calidad del aire:', 0, 40)

#REQUIERE CALIBRACION
    if sensor_aire>25000:
        oled.text('Mala', 40, 50)
    elif sensor_aire <15000:
        oled.text('Muy Buena', 20, 50)
    elif sensor_aire >30000:
        oled.text('Muy Mala', 40, 50)
    else:
        oled.text('Buena', 40, 50)    
        
    oled.show()

#SENTENCIA DE SUBIDA A LA NUBE
    try:
        credenciales = bytes("channels/{:s}/publish".format(str(2768474)), 'utf-8')  #ID CANAL
        sa = bytes("field1={:.1f}&field2={:.1f}&field3={:.1f}\n".format(temp_pantalla, pres_pantalla,sensor_aire), 'utf-8')
        client.publish(credenciales, sa)
        time.sleep(5)
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        wlan.disconnect()
        break

