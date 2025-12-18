# -*- coding: utf-8 -*-
import os
import unittest
import json

from facturacion_electronica import facturacion_electronica as fe
from facturacion_electronica.util_certificado import inyectar_certificado_en_data
from facturacion_electronica.conexion import api_url


class TestBoletaTrackLocal(unittest.TestCase):
    """
    Test local para consultar el estado de un envío de BOLETA (API) usando un TRACK_ID.
    Requiere variables de entorno:
      - TRACK_ID: track devuelto por el SII al enviar boletas
      - PFX_PATH, PFX_PASS, RUT_FIRMANTE
    Opcional:
      - MODO: 'certificacion' (default) o 'produccion'
    """

    def test_consulta_estado_envio_boleta_track(self):
        print("\n=== FLUJO: TRACKING BOLETA (consulta estado envío) ===")
        print("[track] Objetivo: consultar el estado del EnvioBOLETA en SII usando TRACK_ID.")
        print("[track] Nota: este test solo imprime pasos; NO modifica la lógica de tracking.")

        proyecto_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        ejemplo_39 = os.path.join(
            proyecto_root,
            "facturacion_electronica",
            "ejemplos",
            "ejemplo_basico_39.json",
        )
        # Defaults si no hay variables de entorno
        track_id = os.environ.get("TRACK_ID", "25839050")
        pfx_path = os.environ.get(
            "PFX_PATH",
            os.path.abspath(os.path.join(
                proyecto_root,
                "facturacion_electronica/certificados/certificado-totaltools.pfx"
            ))
        )
        pfx_pass = os.environ.get("PFX_PASS", "LaNueva1609")
        rut_firmante = os.environ.get("RUT_FIRMANTE", "17084686-9")
        modo = os.environ.get("MODO", "certificacion")
        sii_token = os.environ.get("SII_TOKEN") or os.environ.get("TOKEN")

        if not os.path.exists(pfx_path):
            self.skipTest("No se encontró el PFX en: {}".format(pfx_path))
        if not os.path.exists(ejemplo_39):
            self.skipTest("No se encontró ejemplo_basico_39.json")

        with open(ejemplo_39) as f:
            data = json.load(f)
        # Si no se define RUT_EMISOR explícitamente, usar el del JSON base (evita consultar con RUT incorrecto)
        rut_emisor = os.environ.get("RUT_EMISOR") or data.get("Emisor", {}).get("RUTEmisor")
        if not rut_emisor:
            self.skipTest("No se pudo determinar RUT_EMISOR (ni env var ni en ejemplo_basico_39.json)")

        print("[track] proyecto_root:", proyecto_root)
        print("[track] ejemplo_39:", ejemplo_39)
        print("[track] PFX_PATH existe:", os.path.exists(pfx_path))
        print("[track] TRACK_ID:", track_id)
        print("[track] RUT_FIRMANTE:", rut_firmante)
        print("[track] RUT_EMISOR:", rut_emisor)
        print("[track] MODO:", modo)
        print("[track] SII_TOKEN provisto:", bool(sii_token))
        if sii_token:
            print("[track] TOKEN:", sii_token)
        # Ajusta Emisor para consulta (RUT y modo)
        data["Emisor"].update({
            "RUTEmisor": rut_emisor,
            "Modo": modo,
        })
        data["test"] = False
        data["verify"] = True
        # Inyecta firma del PFX
        data = inyectar_certificado_en_data(
            data,
            pfx_path=pfx_path,
            password=pfx_pass,
            rut_firmante=rut_firmante or "76387093-6",
        )

        # Para boletas, la consulta usa API
        vals = {
            "Emisor": data["Emisor"],
            "firma_electronica": data["firma_electronica"],
            "codigo_envio": track_id,
            "api": True,
        }
        if sii_token:
            vals["token"] = sii_token
        # Imprime URL que se consultará (referencial)
        rut = data["Emisor"]["RUTEmisor"]
        url_ref = '{0}boleta.electronica.envio/{1}-{2}-{3}'.format(
            api_url[data["Emisor"]["Modo"]],
            rut[:-2],
            rut[-1],
            track_id,
        )
        print("\n[track] Paso 1/2: Preparar request HTTP")
        print("[track] - Método: GET")
        print("[track] - Endpoint:", url_ref)
        print("[track] - Headers esperados por SII: Accept=application/json, Cookie: TOKEN=<token>")
        print("[track] URL consulta (referencial):", url_ref)

        print("\n[track] Paso 2/2: Ejecutar consulta y mostrar respuesta")
        resp = fe.consulta_estado_envio(vals)
        print("[track] Respuesta:", resp)

        # Asserts básicos
        self.assertIn("status", resp)
        self.assertIn("xml_resp", resp)
        # Si hay errores, no fallamos el test - mostramos para diagnóstico
        if resp.get("errores"):
            print("[track] Errores:", resp["errores"])

        print("\n=== FIN FLUJO TRACKING ===\n")


if __name__ == '__main__':
    unittest.main()


