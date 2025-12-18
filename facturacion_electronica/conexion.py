# -#- coding: utf-8 -#-
import collections
from datetime import datetime
from lxml import etree
import codecs
import json
import time
import ssl
from facturacion_electronica import clase_util as util

import logging
_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
except ImportError:
    print('Cannot import ZEEP')

try:
    import urllib3
    pool = urllib3.PoolManager(timeout=30)
except:
    raise UserError('Error en cargar urllib3')
try:
    from requests import Session
except:
    raise UserError("No se puede cargar Session")
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception as e:
    _logger.warning("error en crear Exception %s" %str(e))

server_url = {
    'certificacion': 'https://maullin.sii.cl/',
    'produccion': 'https://palena.sii.cl/'
}

api_url = {
    'certificacion': 'https://apicert.sii.cl/recursos/v1/',
    'produccion': 'https://api.sii.cl/recursos/v1/'
}

api_url_envio = {
    'certificacion': 'https://pangal.sii.cl/recursos/v1/',
    'produccion': 'https://rahue.sii.cl/recursos/v1/'
}

claim_url = {
    'certificacion': 'https://ws2.sii.cl/WSREGISTRORECLAMODTECERT/registroreclamodteservice',
    'produccion': 'https://ws1.sii.cl/WSREGISTRORECLAMODTE/registroreclamodteservice',
}

connection_status = {
    '0': 'Upload OK',
    '1': 'El Sender no tiene permiso para enviar',
    '2': 'Error en tamaño del archivo (muy grande o muy chico)',
    '3': 'Archivo cortado (tamaño <> al parámetro size)',
    '5': 'No está autenticado',
    '6': 'Empresa no autorizada a enviar archivos',
    '7': 'Esquema Invalido',
    '8': 'Firma del Documento',
    '9': 'Sistema Bloqueado',
    'Otro': 'Error Interno.',
}


class UserError(Exception):
    _logger.info(Exception)
    #código que detiene la ejecución
    pass


class Conexion(object):

    def __init__(self, emisor=None, firma_electronica=None, api=False, token=None):
        self.Emisor = emisor
        self.api = api
        if not self.Emisor:
            return
        if not self.Emisor.Modo:
            raise UserError("Not Service provider selected!")
        self.firma = firma_electronica
        # Permitir inyectar un token ya obtenido, para evitar regenerarlo
        # (útil en tracking cuando quieres reutilizar el mismo TOKEN del envío).
        if token:
            try:
                self._token = token
            except Exception:
                pass
        try:
            if not self.token:
                self.token = True
        except:
            pass

    @property
    def api(self):
        if not hasattr(self, '_api'):
            return False
        return self._api

    @api.setter
    def api(self, val=False):
        self._api = val

    @property
    def cesion(self):
        if not hasattr(self, '_cesion'):
            return False
        return self._cesion

    @cesion.setter
    def cesion(self, val):
        self._cesion = val

    @property
    def destino(self):
        if self.api:
            return 'boleta.electronica.envio'
        if self.cesion:
            return 'cgi_rtc/RTC/RTCAnotEnvio.cgi'
        return 'cgi_dte/UPL/DTEUpload'

    @property
    def Emisor(self):
        if not hasattr(self, '_emisor'):
            return False
        return self._emisor

    @Emisor.setter
    def Emisor(self, val):
        self._emisor = val

    @property
    def seed(self):
        if not hasattr(self, '_seed') or not self._seed:
            return False
        xml_seed = u'<getToken><Semilla>%s</Semilla></getToken>' \
            % (self._seed)
        if self.api:
            xml_seed = u'<getToken><item ID="IdAFirmar"><Semilla>%s</Semilla></item></getToken>' \
                % (self._seed)
            return  self.firma.firmar(xml_seed, uri="IdAFirmar", type="token")
        return  self.firma.firmar(xml_seed, type="token")

    @seed.setter
    def seed(self, val):
        if not val:
            return
        url = server_url[self.Emisor.Modo] + 'DTEWS/CrSeed.jws?WSDL'
        if self.api:
            url = api_url[self.Emisor.Modo] + 'boleta.electronica.semilla'
            req = pool.request('GET', url, headers={
                'Accept': "application/xml"})
            resp = req.data.decode('UTF-8')
        else:
            _server = self._client(url)
            intent = 0
            resp = False
            while intent < 10 and not resp:
                intent += 1
                try:
                    resp = _server.service.getSeed()
                except Exception as e:
                    time.sleep(1)
        root = etree.fromstring(resp.replace(
                '<?xml version="1.0" encoding="UTF-8"?>', ''))
        self._seed = root[0][0].text

    @property
    def token(self):
        if not hasattr(self, '_token'):
            return False
        return self._token

    @token.setter
    def token(self, val):
        if not val:
            return False
        self.seed = True
        url = server_url[self.Emisor.Modo] + 'DTEWS/GetTokenFromSeed.jws?WSDL'
        if self.api:
            url = api_url[self.Emisor.Modo] + 'boleta.electronica.token'
            seed = '<?xml version="1.0" encoding="UTF-8"?>' + self.seed
            req = pool.request('POST', url, body=seed, headers={
                'Accept': "application/xml",
                "Content-Type": "application/xml"})
            resp = req.data.decode('UTF-8')
        else:
            _server = self._client(url)
            intent = 0
            resp = False
            while intent < 10 and not resp:
                intent += 1
                try:
                    resp = _server.service.getToken(self.seed)
                except Exception as e:
                    time.sleep(1)
        respuesta = etree.fromstring(resp.replace(
                '<?xml version="1.0" encoding="UTF-8"?>', ''))
        self._token = respuesta[0][0].text

    def init_params(self):
        params = collections.OrderedDict()
        if self.cesion:
            params['emailNotif'] = self.Emisor.CorreoEmisor
        else:
            params['rutSender'] = self.firma.rut_firmante[:-2]
            params['dvSender'] = self.firma.rut_firmante[-1]
        params['rutCompany'] = self.Emisor.RUTEmisor[:-2]
        params['dvCompany'] = self.Emisor.RUTEmisor[-1]
        return params

    def send_xml_file(self, envio_dte=None, file_name="envio"):
        if not self.token:
            raise UserError("No hay Token")
        base = server_url[self.Emisor.Modo]
        if self.api:
            base = api_url_envio[self.Emisor.Modo]
        url = "%s%s" % (
            base,
            self.destino
        )

        headers = {
            'Accept': 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*',
            'Accept-Language': 'es-cl',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; PROG 1.0; Windows NT 5.0; YComp 5.0.2.4)',
            'Referer': '{}'.format(self.Emisor.Website),
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
            'Cookie': 'TOKEN={}'.format(self.token),
        }
        if self.api:
            headers['Accept'] = 'application/json'
        params = self.init_params()
        params['archivo'] = (
                    file_name,
                    '<?xml version="1.0" encoding="ISO-8859-1"?>\n%s'\
                    % envio_dte,
                    "text/xml")
        urllib3.filepost.writer = codecs.lookup('ISO-8859-1')[3]
        multi = urllib3.filepost.encode_multipart_formdata(params)
        try:
            headers.update({'Content-Length': '{}'.format(len(multi[0]))})
            response = pool.request_encode_body(
                                        'POST',
                                        url,
                                        params,
                                        headers
                                    )
        except Exception as e:
            _logger.warning("e %s" %str(e))
            return {'status': 'NoEnviado', 'xml_resp': str(e)}
        if self.api:
            resp = json.loads(response.data.decode('ISO-8859-1'))
            return {
                'sii_xml_response': response.data,
                'status': util.estado_envio(resp.get('estado')),
                'sii_send_ident': resp.get('trackid'),
                'estado_sii': resp.get('estado'),
            }
        retorno = {
                'sii_xml_response': response.data.decode(),
                'status': 'NoEnviado',
                'sii_send_ident': '',
                }
        if response.status != 200:
            return retorno
        respuesta_dict = etree.fromstring(response.data)
        code = respuesta_dict.find('STATUS').text
        if code != '0':
            _logger.warning(connection_status[code])
            if code in ['7', '106']:
                retorno['sii_result'] = 'Rechazado'
        else:
            retorno.update({
                'status': 'Enviado',
                'sii_send_ident': respuesta_dict.find('TRACKID').text
                })
        return retorno

    def consulta_estado_envio(self, track_id):
        resultado = {
            'status': 'Enviado',
            'xml_resp': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en consulta envío")
            return resultado
        rut = self.Emisor.RUTEmisor
        if self.api:
            url = '{0}boleta.electronica.envio/{1}-{2}-{3}'.format(
                            api_url[self.Emisor.Modo],
                            rut[:-2],
                            rut[-1],
                            track_id
                        )
            headers = {
                'Accept': 'application/json',
                'Cookie': 'TOKEN={}'.format(self.token),
            }
            try:
                response = pool.request(
                        'GET',
                        url,
                        headers=headers
                    )
                raw = response.data or b""
                text = raw.decode('ISO-8859-1', errors='replace')
                self.sii_message = text

                # Mantener compatibilidad con callers: retornamos "status" y adjuntamos detalle de error.
                if response.status == 404:
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': text,
                        'errores': [f"HTTP 404 (no encontrado) al consultar envío: {url}"],
                    }
                if response.status != 200:
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': text,
                        'errores': [f"HTTP {response.status} al consultar envío: {url}"],
                    }
                if not raw:
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': '',
                        'errores': [f"Respuesta vacía del SII al consultar envío: {url}"],
                    }
                # A veces el SII responde 200 con solo espacios/saltos de línea.
                # Eso no es JSON válido y antes terminaba en JSONDecodeError.
                if not text.strip():
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': text,
                        'errores': [f"Respuesta vacía (solo espacios) del SII al consultar envío: {url}"],
                    }

                # SII debería responder JSON; si llega HTML u otro contenido, evitamos JSONDecodeError
                content_type = ""
                try:
                    content_type = (response.headers.get("Content-Type") or "").lower()
                except Exception:
                    content_type = ""
                looks_json = ("application/json" in content_type) or text.lstrip().startswith(("{", "["))
                if not looks_json:
                    preview = text.strip().replace("\n", " ")[:200]
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': text,
                        'errores': [f"Respuesta no-JSON del SII (Content-Type='{content_type}'): {preview}"],
                    }

                try:
                    resp = json.loads(text)
                except Exception as e:
                    preview = text.strip().replace("\n", " ")[:200]
                    return {
                        'status': 'Enviado',
                        'detalles': '',
                        'detalle_rep_rech': [],
                        'xml_resp': text,
                        'errores': [f"Error parseando JSON del SII: {e}. Content-Type='{content_type}'. Preview: {preview}"],
                    }
                return {
                    'status': util.estado_envio(resp.get('estado'), resp.get('estadistica')),
                    'detalles': resp.get('estadistica'),
                    'detalle_rep_rech': resp.get('detalle_rep_rech'),
                    'xml_resp': text,
                }
            except Exception as e:
                resultado['detalle_rep_rech'] = []
                resultado['errores'].append(str(e))
                return resultado
        url = server_url[self.Emisor.Modo] + 'DTEWS/QueryEstUp.jws?WSDL'
        if self.cesion:
            url = server_url[self.Emisor.Modo] + 'DTEWS/services/wsRPETCConsulta?wsdl'
        try:
            _server = self._client(url)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                if self.cesion:
                    respuesta = _server.service.getEstEnvio(
                                self.token,
                                track_id
                            )
                else:
                    respuesta = _server.service.getEstUp(
                                rut[:-2],
                                str(rut[-1]),
                                track_id,
                                self.token
                            )
            except Exception as e:
                time.sleep(1)
                resultado['errores'].append(str(e))
        if not respuesta:
            resultado['errores'].append("No se obtuvo respuesta")
            return resultado
        self.sii_message = respuesta
        return util.procesar_respuesta_envio(respuesta)

    def reenvio_correo_envio(self, track_id):
        resultado = {
            'status': 'NoEnviado',
            'xml_resp': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en reenvío correo")
            return resultado
        url = server_url[self.Emisor.Modo] + 'DTEWS/services/wsDTECorreo?wsdl'
        rut = self.Emisor.RUTEmisor
        try:
            _server = self._client(url)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                respuesta = _server.service.reenvioCorreo(
                    self.token,
                    rut[:-2],
                    str(rut[-1]),
                    track_id,
                )
            except Exception as e:
                time.sleep(1)
        if not respuesta:
            resultado['errores'].append("No se obtuvo respuesta")
            return resultado
        self.sii_message = respuesta
        return util.procesar_respuesta_envio(respuesta)

    def consulta_estado_dte(self, doc):
        resultado = {
            'status': 'Enviado',
            'xml_resp': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en consulta DTE")
            return resultado
        receptor = doc._receptor.RUTRecep
        fecha = datetime.strptime(doc.FechaEmis, "%Y-%m-%d").strftime("%d-%m-%Y")
        if self.api:
            url = '{0}boleta.electronica/{1}-{2}-{3}-{4}/estado?rut_receptor={5}&dv_receptor={6}&monto={7}&fechaEmision={8}'.format(
                        api_url[self.Emisor.Modo],
                        self.Emisor.RUTEmisor[:-2],
                        self.Emisor.RUTEmisor[-1],
                        doc.TipoDTE,
                        doc.Folio,
                        receptor[:-2],
                        receptor[-1],
                        doc.MntTotal,
                        fecha,
                    )
            headers = {
                'Accept': 'application/json',
                'Cookie': 'TOKEN={}'.format(self.token),
            }
            response = pool.request(
                    'GET',
                    url,
                    headers=headers
                )
            if response.status == 404:
                resultado['detalle_rep_rech'] = []
                resultado['errores'].append("404 error")
                return resultado
            resp = json.loads(response.data.decode('ISO-8859-1'))
            return {
                'glosa': resp['descripcion'],
                'status': util.estado_documento(resp['codigo']),
                'xml_resp': response.data.decode('ISO-8859-1'),
            }
        url = server_url[self.Emisor.Modo] + 'DTEWS/QueryEstDte.jws?WSDL'
        if self.cesion:
            url = server_url[self.Emisor.Modo] + 'DTEWS/services/wsRPETCConsulta?wsdl'
        try:
            _server = self._client(url)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        rut = self.firma.rut_firmante
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                if self.cesion:
                    """ Consulta para Emitidas. Se debe obtener IdCesion, para consulta avanzada """
                    respuesta = _server.service.getEstCesion(
                        self.token,
                        self.Emisor.RUTEmisor[:-2],
                        str(self.Emisor.RUTEmisor[-1]),
                        str(doc.TipoDTE),
                        str(doc.Folio),
                        doc.IdCesion,
                    )
                else:
                    respuesta = _server.service.getEstDte(
                        rut[:-2],
                        str(rut[-1]),
                        self.Emisor.RUTEmisor[:-2],
                        str(self.Emisor.RUTEmisor[-1]),
                        receptor[:-2],
                        str(receptor[-1]),
                        str(doc.TipoDTE),
                        str(doc.Folio),
                        fecha,
                        str(doc.MntTotal),
                        self.token
                    )
            except Exception as e:
                time.sleep(1)
                if intent == 10:
                    _logger.warning("error en consulta", exc_info=True)
        if not respuesta:
            resultado['detalle_rep_rech'] = []
            resultado['errores'].append("No se pudo obtener estado DTE")
            return resultado
        return util.procesar_respuesta_dte(respuesta, self.cesion)

    def consulta_estado_cesion_relac(self, doc):
        """ Esta consulta es para facturas de proveedores """
        resultado = {
            'status': 'Enviado',
            'xml_resp': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en consulta cesion DTE relac")
            return resultado
        url = server_url[self.Emisor.Modo] + 'DTEWS/services/wsRPETCConsulta?wsdl'
        try:
            _server = self._client(url)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        rut = doc.Emisor.RUTEmisor
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                respuesta = _server.service.getEstCesionRelac(
                    self.token,
                    rut[:-2],
                    str(rut[-1]),
                    str(doc.TipoDTE),
                    str(doc.Folio),
                    doc._receptor.RUTRecep[:-2],
                    doc._receptor.RUTRecep[-1]
                )
            except Exception as e:
                time.sleep(1)
                if intent == 10:
                    _logger.warning("error en consulta", exc_info=True)
        if not respuesta:
            resultado['detalle_rep_rech'] = []
            resultado['errores'].append("No se pudo obtener estado cesion DTE relac")
            return resultado
        return util.procesar_respuesta_dte(respuesta, True)

    def sign_claim(self, claim):
        doc = etree.fromstring(claim)
        signed_node = self.firma.firmar(doc)
        msg = etree.tostring(
            signed_node, pretty_print=True)
        return msg
        self.seed_file = msg

    def _client(self, url, use_token=False):
        session = Session()
        if use_token:
            session.headers['Cookie'] = 'TOKEN=' + self.token
        transport = Transport(timeout=10, session=session)
        return Client(
            url,
            transport=transport
            )

    def set_dte_claim(self, doc):
        resultado = {
            'status': 'Enviado',
            'respuesta': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en set claim")
            return resultado
        url = claim_url[self.Emisor.Modo]+'?wsdl'
        try:
            _server = self._client(url, True)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                respuesta = _server.service.ingresarAceptacionReclamoDoc(
                    doc['RUTEmisor'][:-2],
                    str(doc['RUTEmisor'][-1]),
                    str(doc['TipoDTE']),
                    str(doc['Folio']),
                    doc['Claim']
                )
            except Exception as e:
                time.sleep(1)
                if intent == 10:
                    _logger.warning("error en set claim", exc_info=True)
        resultado['respuesta'] = respuesta
        return resultado

    def get_dte_claim(self, doc):
        resultado = {
            'status': 'Enviado',
            'xml_resp': '',
            'errores': []
        }
        if not self.token:
            resultado['errores'].append("No hay Token en consulta claim")
            return resultado
        url = claim_url[self.Emisor.Modo]+'?wsdl'
        try:
            _server = self._client(url, True)
        except Exception as e:
            resultado['errores'].append(str(e))
            return resultado
        intent = 0
        respuesta = False
        while intent < 10 and not respuesta:
            intent += 1
            try:
                respuesta = _server.service.listarEventosHistDoc(
                    doc['RUTEmisor'][:-2],
                    str(doc['RUTEmisor'][-1]),
                    str(doc['TipoDTE']),
                    str(doc['Folio']),)
            except Exception as e:
                time.sleep(1)
                if intent == 10:
                    _logger.warning("error en get claim", exc_info=True)
        resultado['respuesta'] = respuesta
        return resultado
