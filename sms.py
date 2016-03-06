import SOAPpy
import pysftp
import os

import psycopg2
import xlrd


PRODUCTION = True
PATH = 'media/'

def leer_desde_txt(file_name):
    with open(file_name, 'r') as f:
        items = [line.strip() for line in f]
    return items

def leer_desde_xls(file_name):
    try:
        with xlrd.open_workbook(file_name) as wb:
            worksheet = wb.sheet_by_index(0)
            num_rows, curr_row = worksheet.nrows, 0  # - 1
            data = []
            while curr_row < num_rows:
                cell_value = worksheet.cell_value(curr_row, 0)
                data.append(str(cell_value))
                curr_row += 1
            return data
    except Exception as e:
        print 'Error al leer archivo xls', e


class SendInvoiceXML(object):
    def __init__(self, db_name, db_user, db_pwd):
        self.db_name = db_name
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.cursor = None
        self.cxn = None

    def connect(self):
        try:
            dns = "host=%s port='5432' dbname='%s' user='%s' password='%s'" % ('192.168.0.16',
                                                                               'innobee_portal_buzon',
                                                                               'postgres',
                                                                               'postgres')
            # logging.debug('Cadena de conexion ' + dns)
            self.cxn = psycopg2.connect(dns)
            self.cursor = self.cxn.cursor()
            print 'Conectado OK'
        except Exception as e:
            # logging.error('No se puede conectarse a la BDD ' + str(e))
            print 'Error al conectar: ' + str(e)


    def disconnect(self):
        self.cursor.close()
        if self.cxn:
            self.cxn.close()

    def run_query(self, query):
        # self.connect()
        self.cursor.execute(query)

        if query.upper().startswith('SELECT'):
            result = self.cursor.fetchall()
        else:
            self.cxn.commit()
            result = None

        #self.disconnect()

        return result


def enviar_SMS(receptores, mensaje):
    global numero_telefonico
    try:
        PUBLIMES_WS_URL = 'http://online.publimes.com:5000/Service.svc'
        PUBLIMES_WS_NAMESPACE = 'http://tempuri.org/'
        PUBLIMES_WS_CREATE_ACTION = 'http://tempuri.org/IService/EnviarMensaje'
        PUBLIMES_WS_CLIENT = '122'
        PUBLIMES_WS_PWD = 'QSTF5693'
        PUBLIMES_WS_OPERADORA = 'C'

        from django.conf import settings

        print 'enviar_SMS - Conectando WS PUBLIMES...'
        proxy = SOAPpy.SOAPProxy(PUBLIMES_WS_URL, namespace=PUBLIMES_WS_NAMESPACE,
                                 soapaction=PUBLIMES_WS_CREATE_ACTION)

        namespace = PUBLIMES_WS_NAMESPACE

        print 'enviar_SMS - Conectados!'
        proxy.config.debug = 1
        for numero_telefonico in receptores:
            print 'enviar_SMS - Enviando mensaje a', numero_telefonico
            resp = proxy.EnviarMensaje(SOAPpy.Types.untypedType(name=(namespace, "idCliente"), data=PUBLIMES_WS_CLIENT),
                                       SOAPpy.Types.untypedType(name=(namespace, "contrasenia"), data=PUBLIMES_WS_PWD),
                                       SOAPpy.Types.untypedType(name=(namespace, "operadora"),
                                                                data=PUBLIMES_WS_OPERADORA),
                                       SOAPpy.Types.untypedType(name=(namespace, "numeroTelefonico"),
                                                                data=numero_telefonico),
                                       SOAPpy.Types.untypedType(name=(namespace, "mensaje"), data=mensaje))
            print 'enviar_SMS - Mensaje enviado! ' + resp
    except Exception as e:
        print 'enviar_SMS - Error', e


def main():
    db_process = SendInvoiceXML('onepago', 'postgres', 'postgres')
    db_process.connect()
    DATA = db_process.run_query("SELECT id_campania_sms, ruc_empresa, receptor_sms_archivo, mensaje FROM publicidad.campania_sms where fecha_publicacion <= now() and estado=1 order by fecha_creacion limit 1")
    if DATA and len(DATA) == 1:
        ruta_archivo = str(DATA[0][2]).lower()
        try:
            if ruta_archivo.find('.xls') != -1:
                TELEFONOS = leer_desde_xls(PATH + str(DATA[0][2]))
            elif ruta_archivo.find('.txt') != -1:
                TELEFONOS = leer_desde_txt(PATH + str(DATA[0][2]))
            else:
                db_process.disconnect()
                return -1
            if len(TELEFONOS) > 0:
                enviar_SMS(TELEFONOS, DATA[0][3])
                DATA = db_process.run_query("update publicidad.campania_sms set estado=2 where id_campania_sms=" + str(DATA[0][0]))
        except Exception as e:
            print e
            print ruta_archivo
            return -1
    else:
        return 0
    db_process.disconnect()
    return 1

#print main()
TELEFONOS = leer_desde_txt('/home/dario/Escritorio/tel.txt')
print TELEFONOS