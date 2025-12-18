# -*- coding: utf-8 -*-
import os
import json
from typing import Dict, Any
import copy
import base64

from facturacion_electronica import facturacion_electronica as fe
from facturacion_electronica import clase_util as util
from facturacion_electronica.util_certificado import (
    inyectar_certificado_en_data,
    inyectar_caf_en_data,
)
from facturacion_electronica.emisor import Emisor
from facturacion_electronica.firma import Firma
from facturacion_electronica.conexion import Conexion, api_url, api_url_envio


def cargar_json(path_json: str) -> Dict[str, Any]:
    with open(path_json) as f:
        return json.load(f)

def main():
    # Rutas/credenciales (preferir env vars para no hardcodear):
    # - PFX_PATH, PFX_PASS, RUT_FIRMANTE
    # - CAF39_PATH
    ejemplo_json_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "ejemplos/ejemplo_basico_39.json"
    ))
    pfx_path = os.environ.get("PFX_PATH") or os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "certificados/Certificado E-Certchile.pfx",
    ))
    pfx_pass = os.environ.get("PFX_PASS") or "LaNueva1609"
    rut_firmante = os.environ.get("RUT_FIRMANTE") or "17084686-9"
    # CAF a usar para boleta (TipoDTE=39).
    caf39_path = os.environ.get("CAF39_PATH") or os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "Folios/CAF39.xml",
    ))
    # Control opcional para DEMO/TEST: limitar cuántas boletas (documentos) enviar.
    # - Si no se define, se envían todas las del JSON (por defecto el ejemplo trae 2).
    # - Si defines MAX_DTES=1, se enviará solo 1 boleta (sin afectar la lógica core).
    max_dtes_env = os.environ.get("MAX_DTES")
    max_dtes = int(max_dtes_env) if (max_dtes_env and str(max_dtes_env).strip()) else None

    print("\n=== FLUJO: EMISIÓN BOLETA RÁPIDA (DTE 39) ===")
    print("[boleta] Objetivo: timbrar 1..N boletas, armar EnvioBOLETA, enviarlo al SII, obtener TRACKID y luego poder hacer tracking.")
    print("[boleta] Nota: este script imprime pasos y endpoints; NO cambia la lógica de negocio.")

    print("[boleta] ejemplo_json_path:", ejemplo_json_path)
    print("[boleta] pfx_path existe:", os.path.exists(pfx_path))
    print("[boleta] caf39_path existe:", os.path.exists(caf39_path))
    print("[boleta] Modo (ambiente): certificacion/produccion =>", "certificacion")
    print("[boleta] CAF39_PATH (ruta):", caf39_path)
    print("[boleta] MAX_DTES:", max_dtes if max_dtes is not None else "(sin límite; usa lo que venga en el JSON)")

    print("\n[boleta] Paso 1/6: Cargar 'input' base desde JSON de ejemplo")
    data = cargar_json(ejemplo_json_path)

    # (Opcional) Limitar cantidad de documentos por grupo (p.ej. TipoDTE 39)
    if max_dtes is not None:
        try:
            for g in data.get("Documento", []):
                if isinstance(g, dict) and isinstance(g.get("documentos"), list):
                    g["documentos"] = g["documentos"][:max_dtes]
            print("[boleta] (demo) Se limitaron los documentos por grupo a MAX_DTES =", max_dtes)
        except Exception as e:
            print("[boleta] (demo) No se pudo aplicar MAX_DTES (se ignora):", str(e))

    print("[boleta] Paso 2/6: Ajustar datos del Emisor y flags de ejecución")
    # Emisor (ajustado a tus datos)
    data["Emisor"].update({
        "RUTEmisor": "76387093-6",
        "RznSoc": "INVERSIONES LUIS ANDRÉS ZUÑIGA CASTILLO",
        "GiroEmis": "FONDOS Y SOCIEDADES DE INVERSION Y ENTIDADES FINANCIERAS SIMILARES",
        "DirOrigen": "VICTORIA #1543",
        "CmnaOrigen": "SANTIAGO",
        "CiudadOrigen": "SANTIAGO",
        "Modo": "certificacion",  # cambia a 'produccion' para ambiente real
    })
    data["test"] = False   # False => genera seed/token y envía
    data["verify"] = True

    # Ajusta fechas de emisión de boletas (FchEmis) a hoy para evitar error 647
    # y fuerza Folio=0 para asignación automática (toma el siguiente folio del CAF cargado)
    print("[boleta] Paso 3/6: Normalizar fechas y forzar auto-folio (Folio=0)")
    hoy = util.time_stamp('%Y-%m-%d')
    grupos = data.get("Documento", [])
    actualizados = []
    for g in grupos:
        if int(g.get("TipoDTE", 0)) == 39:
            for d in g.get("documentos", []):
                try:
                    iddoc = d.setdefault("Encabezado", {}).setdefault("IdDoc", {})
                    iddoc["FchEmis"] = hoy
                    # El JSON de ejemplo trae folios fijos (p.ej. 37/38). Para usar el CAF vigente
                    # (p.ej. 801-900), dejamos Folio=0 y la librería asigna el correlativo.
                    iddoc["Folio"] = 0
                    actualizados.append((g.get("TipoDTE"), d.get("NroDTE"), iddoc.get("Folio")))
                except Exception:
                    pass
    if actualizados:
        print("[boleta] FchEmis actualizado a hoy para DTEs:", actualizados)

    # Inyecta certificado y CAF
    print("[boleta] Paso 4/6: Inyectar PFX (certificado) y CAF (folios) al payload")
    print("[boleta] - PFX: se carga y se convierte a base64 (secreto, no se imprime)")
    print("[boleta] - CAF: se lee desde archivo y se inyecta como base64 (no editar CAF a mano)")
    data = inyectar_certificado_en_data(
        data,
        pfx_path=pfx_path,
        password=pfx_pass,
        rut_firmante=rut_firmante,
    )
    data = inyectar_caf_en_data(
        data,
        tipo_dte=39,
        caf_path=caf39_path,
    )

    # Muestra URLs y genera seed/token
    print("\n[boleta] Paso 5/6: Autenticación SII (SEMILLA -> TOKEN)")
    modo = data["Emisor"]["Modo"]
    url_seed = api_url[modo] + "boleta.electronica.semilla"
    url_token = api_url[modo] + "boleta.electronica.token"
    url_envio = api_url_envio[modo] + "boleta.electronica.envio"
    print("[boleta] - GET  (semilla):", url_seed)
    print("[boleta]   Headers: Accept=application/xml")
    print("[boleta] - POST (token):", url_token)
    print("[boleta]   Headers: Accept=application/xml, Content-Type=application/xml")
    print("[boleta] - POST (envío):", url_envio)
    print("[boleta]   Headers: Cookie: TOKEN=<token> (se imprimirá el token completo)")
    try:
        emisor_obj = Emisor(data["Emisor"])
        # Usa una copia para no mutar data['firma_electronica'] (la clase Firma consume y elimina claves)
        firma_obj = Firma(copy.deepcopy(data["firma_electronica"]))
        conex = Conexion(emisor_obj, firma_obj, api=True)
        conex.token = True
        print("[boleta] seed (raw):", getattr(conex, "_seed", "(no disponible)"))
        print("[boleta] seed firmado (XML):\n", conex.seed)
        print("[boleta] token:", getattr(conex, "_token", "(no disponible)"))
    except Exception as e:
        print("[boleta] No se pudo obtener seed/token de ejemplo:", str(e))

    # Reinyecta credenciales por si fueron consumidas por la clase Firma anterior
    data = inyectar_certificado_en_data(
        data,
        pfx_path=pfx_path,
        password=pfx_pass,
        rut_firmante=rut_firmante,
    )

    # Enviar
    print("\n[boleta] Paso 6/6: Timbrar + Enviar EnvioBOLETA (multipart POST) -> TRACKID")
    print("[boleta] - Se genera el DTE 39, se arma TED/FRMT, se firman Documento(s) y SetDTE, y se envía al SII.")
    resp = fe.timbrar_y_enviar(data)
    print("[boleta] Respuesta keys:", list(resp.keys()))
    # Imprime status y trackid si existen
    if resp.get("status") is not None:
        print("[boleta] status:", resp.get("status"))
    if resp.get("estado_sii") is not None:
        print("[boleta] estado_sii:", resp.get("estado_sii"))
    print("[boleta] trackid:", resp.get("sii_send_ident"))
    if resp.get("errores"):
        print("[boleta] Errores:", resp.get("errores"))
    if resp.get("sii_xml_request"):
        print("[boleta] (debug) XML EnvioBOLETA (completo) a continuación.")
        print("[boleta] XML Envio completo:\n", resp.get("sii_xml_request"))
    if resp.get("detalles"):
        print("[boleta] Detalles enviados:", len(resp.get("detalles")))
        for d in resp.get("detalles", []):
            print("[boleta] Detalle:", {
                "NroDTE": d.get("NroDTE"),
                "TipoDTE": d.get("TipoDTE"),
                "Folio": d.get("Folio"),
                "ok_xml": bool(d.get("sii_xml_dte")),
                "ok_barcode_img": bool(d.get("sii_barcode_img")),
                "error": d.get("error"),
            })
            # Guardar imagen de timbre electrónico (PDF417) si está disponible
            img_b64 = d.get("sii_barcode_img")
            if img_b64:
                try:
                    out_dir = os.environ.get("BARCODE_OUT_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "out", "barcodes"))
                    os.makedirs(out_dir, exist_ok=True)
                    fname = "pdf417_T{0}_F{1}.png".format(d.get("TipoDTE"), d.get("Folio"))
                    out_path = os.path.join(out_dir, fname)
                    png_data = base64.b64decode(img_b64)
                    with open(out_path, "wb") as fpng:
                        fpng.write(png_data)
                    print("[boleta] PDF417 (timbre electrónico) guardado en:", out_path)
                except Exception as e:
                    print("[boleta] No se pudo guardar PDF417:", str(e))

    print("\n=== FIN FLUJO EMISIÓN BOLETA RÁPIDA ===\n")

if __name__ == "__main__":
    main()


