# -*- coding: utf-8 -*-
import base64
import json
from typing import Optional, Dict, Any

from facturacion_electronica import facturacion_electronica as fe


def _leer_pfx_base64(pfx_path: str) -> str:
    with open(pfx_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ISO-8859-1")


def _leer_caf_base64(caf_path: str) -> str:
    with open(caf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ISO-8859-1")


def inyectar_certificado_en_data(
    data: Dict[str, Any],
    pfx_path: str,
    password: str,
    rut_firmante: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inserta el certificado PFX/P12 (en base64) y la contraseña en data['firma_electronica'].
    - pfx_path: ruta absoluta al archivo .pfx/.p12
    - password: contraseña del PFX/P12
    - rut_firmante: opcional, RUT del firmante si deseas forzarlo (formato 11111111-1)
    """
    firma = data.get("firma_electronica", {})
    # Asegura que la password sea bytes-like para evitar problemas en cryptography (py3.13+)
    password_bytes = password.encode("ISO-8859-1") if isinstance(password, str) else password
    firma.update({
        "init_signature": True,
        "string_password": password_bytes,
        "string_firma": _leer_pfx_base64(pfx_path),
    })
    if rut_firmante:
        firma["rut_firmante"] = rut_firmante
    data["firma_electronica"] = firma
    return data


def inyectar_caf_en_data(
    data: Dict[str, Any],
    tipo_dte: int,
    caf_path: Optional[str] = None,
    caf_b64: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inserta el CAF (Base64) para el TipoDTE indicado en data['Documento'].
    - Si entregas caf_path, se leerá y convertirá a Base64.
    - Si entregas caf_b64, se usará directamente.
    """
    if not caf_b64 and caf_path:
        caf_b64 = _leer_caf_base64(caf_path)
    if not caf_b64:
        return data
    documentos = data.get("Documento", [])
    for grupo in documentos:
        if int(grupo.get("TipoDTE", 0)) == int(tipo_dte):
            grupo["caf_file"] = [caf_b64]
    data["Documento"] = documentos
    return data


def cargar_ejemplo_y_enviar(
    ejemplo_json_path: str,
    pfx_path: str,
    password: str,
    rut_firmante: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Carga un JSON de ejemplo, inyecta el PFX y envía al SII (timbrar_y_enviar).
    Retorna el diccionario de respuesta de la librería.
    """
    with open(ejemplo_json_path) as f:
        data = json.load(f)
    data = inyectar_certificado_en_data(
        data,
        pfx_path=pfx_path,
        password=password,
        rut_firmante=rut_firmante,
    )
    return fe.timbrar_y_enviar(data)


def cargar_ejemplo_inyectar_caf_y_enviar(
    ejemplo_json_path: str,
    caf_por_tipo: Dict[int, str],
    pfx_path: str,
    password: str,
    rut_firmante: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Carga un JSON, inyecta PFX y asigna CAF por TipoDTE usando rutas a los XML de CAF.
    caf_por_tipo: { 33: "/ruta/CAF33.xml", 61: "/ruta/CAF61.xml", ... }
    """
    with open(ejemplo_json_path) as f:
        data = json.load(f)
    data = inyectar_certificado_en_data(
        data,
        pfx_path=pfx_path,
        password=password,
        rut_firmante=rut_firmante,
    )
    for tipo, caf_path in caf_por_tipo.items():
        data = inyectar_caf_en_data(data, tipo_dte=int(tipo), caf_path=caf_path)
    return fe.timbrar_y_enviar(data)


def cargar_ejemplo_y_timbrar(
    ejemplo_json_path: str,
    pfx_path: str,
    password: str,
    rut_firmante: Optional[str] = None,
) -> Any:
    """
    Carga un JSON de ejemplo, inyecta el PFX y solo timbra (sin enviar).
    Retorna la lista con los DTE firmados (sii_xml_dte, sii_barcode_img).
    """
    with open(ejemplo_json_path) as f:
        data = json.load(f)
    data = inyectar_certificado_en_data(
        data,
        pfx_path=pfx_path,
        password=password,
        rut_firmante=rut_firmante,
    )
    return fe.timbrar(data)


