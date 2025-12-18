## boleta_rapida_tracking_min

Minimal package to:

- **Issue an Electronic Receipt (Boleta) (DTE 39)** with `emitir_boleta_rapida.py`.
- **Track the submission** (status query by `TRACK_ID`) with `tests/emision/test_boleta_track_local.py`.

> This project calls SII endpoints. You need valid credentials/certificates and internet access.

---

## 1) Requirements

- **Python 3**
- `pip`

Python dependencies (installed via `requirements.txt`): `lxml`, `cryptography`, `requests`, `pdf417gen`, etc.

---

## 2) Environment setup

Project location:

- `boleta_rapida_tracking_min/`

Recommended: create a virtual environment.

```bash
cd "/Users/ivanaburto/Downloads/facturacion_electronica-master/boleta_rapida_tracking_min"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
```

---

## 3) Important files

- **Issuance**: `facturacion_electronica/emitir_boleta_rapida.py`
- **Example input (1 boleta)**: `facturacion_electronica/ejemplos/ejemplo_basico_39.json`
- **Local CAF (boleta 39)**: `facturacion_electronica/Folios/CAF39.xml`
- **Folio state (persistence)**: `facturacion_electronica/out/folio_state.json`
- **Tracking (test)**: `tests/emision/test_boleta_track_local.py`

---

## 4) Environment variables (configuration)

### 4.1 Issuance (boleta rápida)

`emitir_boleta_rapida.py` supports:

- **`PFX_PATH`**: path to the `.pfx/.p12` certificate.
- **`PFX_PASS`**: PFX password.
- **`RUT_FIRMANTE`**: signer RUT.
- **`CAF39_PATH`** (optional): path to the CAF XML. If not set, it uses `facturacion_electronica/Folios/CAF39.xml`.
- **`MAX_DTES`** (optional): limits how many boletas from the JSON are sent (e.g., `1`).
- **`BARCODE_OUT_DIR`** (optional): output folder for PDF417 PNG files.
- **`FOLIO_STATE_PATH`** (optional): path to the JSON file where the last used folio is stored.

> Note: the script **normalizes** `FchEmis` to “today” and forces `Folio=0` so the system assigns the next folio from the CAF (persistent).

---

## 4.3 Example JSON payload (TEST ONLY / template)

The file `facturacion_electronica/ejemplos/ejemplo_basico_39.json` is a **testing input**.
During real execution, the script **injects** credentials (PFX/CAF) and **overrides** some fields (folio/date/emisor/flags).

Example “body” JSON **documented** (the `__...__` strings indicate what is injected or overridden):

```json
{
  "ID": "EjemploBasico39",
  "test": "__SE_PISA_EN_SCRIPT__ (emitir_boleta_rapida.py => false para enviar real)",
  "verify": "__SE_PISA_EN_SCRIPT__ (emitir_boleta_rapida.py => true)",
  "Emisor": {
    "RUTEmisor": "__SE_PISA_EN_SCRIPT__ (data['Emisor'].update)",
    "RznSoc": "__SE_PISA_EN_SCRIPT__",
    "GiroEmis": "__SE_PISA_EN_SCRIPT__",
    "DirOrigen": "__SE_PISA_EN_SCRIPT__",
    "CmnaOrigen": "__SE_PISA_EN_SCRIPT__",
    "CiudadOrigen": "__SE_PISA_EN_SCRIPT__",
    "Modo": "__SE_PISA_EN_SCRIPT__ (certificacion/produccion)",
    "NroResol": 0,
    "FchResol": "2018-07-18",
    "ValorIva": 19
  },
  "firma_electronica": {
    "rut_firmante": "__SE_INYECTA_DESDE_PFX__ (RUT_FIRMANTE)",
    "init_signature": "__SE_INYECTA_DESDE_PFX__ (true)",
    "string_password": "__SE_INYECTA_DESDE_PFX__ (PFX_PASS; en runtime queda como bytes ISO-8859-1)",
    "string_firma": "__SE_INYECTA_DESDE_PFX__ (PFX_PATH leído y convertido a base64)"
  },
  "Documento": [
    {
      "TipoDTE": 39,
      "caf_file": [
        "__SE_INYECTA_DESDE_CAF_XML__ (CAF39_PATH -> base64 del CAF, NO editar a mano)"
      ],
      "documentos": [
        {
          "NroDTE": 1,
          "IndServicio": 3,
          "Encabezado": {
            "IdDoc": {
              "Folio": "__SE_PISA_EN_SCRIPT__ (se fuerza 0 para auto-folio desde CAF + folio_state.json)",
              "FchEmis": "__SE_PISA_EN_SCRIPT__ (se fuerza a hoy YYYY-MM-DD)"
            },
            "Receptor": {
              "RUTRecep": "66666666-6",
              "RznSocRecep": "Sin RUT",
              "DirRecep": "Santiago",
              "CmnaRecep": "Santiago"
            }
          },
          "Detalle": [
            {
              "NmbItem": "Producto 1",
              "QtyItem": 1,
              "UnmdItem": "UN",
              "PrcItem": 1000,
              "Impuesto": [
                {
                  "CodImp": 14,
                  "price_include": true,
                  "TasaImp": 19.0
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

Summary (what changes vs what is constant):

- **Constant (business data)**: `Receptor`, `Detalle`, `IndServicio`, `NroDTE`, `TipoDTE`, `ID`, `ValorIva` (and other stable metadata).
- **Overridden/normalized during issuance**: key `Emisor.*`, `Encabezado.IdDoc.FchEmis` (to today), `Encabezado.IdDoc.Folio` (to 0 for auto-folio).
- **Injected**: `firma_electronica.*` (from PFX) and `Documento[].caf_file` (from the CAF XML).

### 4.2 Tracking (submission status query)

The test `tests/emision/test_boleta_track_local.py` supports:

- **`TRACK_ID`**: track returned by SII when sending.
- **`SII_TOKEN`** (optional): if provided, tracking reuses that token (otherwise it attempts to obtain one using the PFX).
- **`MODO`** (optional): `certificacion` (default) or `produccion`.
- **`RUT_EMISOR`** (optional): if not provided, it uses the one from the JSON.
- **`PFX_PATH`**, **`PFX_PASS`**, **`RUT_FIRMANTE`**: used to sign/obtain token when needed.

---

## 5) Issuance step-by-step

### 5.1 (Optional) Set environment variables

Example:

```bash
export PFX_PATH="/ruta/a/tu_certificado.pfx"
export PFX_PASS="TU_PASSWORD"
export RUT_FIRMANTE="11111111-1"

# Optional: use another CAF
# export CAF39_PATH="/ruta/a/tu_CAF39.xml"

# Optional: send only 1 boleta
export MAX_DTES=1
```

### 5.2 Run issuance

From the `boleta_rapida_tracking_min/` root folder:

```bash
cd "/Users/ivanaburto/Downloads/facturacion_electronica-master/boleta_rapida_tracking_min"
python3 -m facturacion_electronica.emitir_boleta_rapida
```

Expected output:

- Seed/token logs
- Submission logs (multipart)
- A `trackid` printed as `sii_send_ident` (this is your `TRACK_ID` for tracking)

---

## 6) Tracking step-by-step

### 6.1 Export TRACK_ID

```bash
export TRACK_ID="TU_TRACK_ID"
```

### 6.2 (Optional) Reuse token

If you already have a valid token and want to **reuse the same**:

```bash
export SII_TOKEN="TU_TOKEN"
```

### 6.3 Run tracking

From the `boleta_rapida_tracking_min/` root folder:

```bash
cd "/Users/ivanaburto/Downloads/facturacion_electronica-master/boleta_rapida_tracking_min"
python3 -m unittest tests.emision.test_boleta_track_local
```

The full response is printed to the console.

---

## 7) Expected responses (correct implementation)

This section summarizes **what you should see** when issuance and tracking are correctly implemented.

### 7.1 Issuance OK (boleta sent to SII)

`python3 -m facturacion_electronica.emitir_boleta_rapida` prints and/or returns a dict with keys typically like:

- **`status`**: `"Enviado"`
- **`estado_sii`**: typically `"REC"` (received)
- **`sii_send_ident`**: the **TRACK_ID** (real example: `25873531`)
- **`detalles`**: per-boleta list, including `TipoDTE`, `NroDTE`, `Folio`, etc.
- **`errores`**: empty list or `None` when everything is OK

Real example (summarized) of correct issuance:

```json
{
  "status": "Enviado",
  "estado_sii": "REC",
  "sii_send_ident": "25873531",
  "detalles": [
    {
      "TipoDTE": 39,
      "NroDTE": 1,
      "Folio": 808,
      "error": null
    }
  ],
  "errores": []
}
```

Notes:

- `estado_sii` being **`REC`** means “received”; it **does not guarantee** final acceptance (final status is seen in tracking).
- The final **folio** (e.g., `808`) is assigned by the CAF (auto-folio) and persisted into `facturacion_electronica/out/folio_state.json`.

### 7.2 Tracking OK (submission status query)

`python3 -m unittest tests.emision.test_boleta_track_local` prints and returns a dict with at least:

- **`status`**: e.g., `"Aceptado"` (human-friendly string built by the library)
- **`xml_resp`**: raw SII response body as a string (in your run it was a JSON-string)
- **`detalles`**: per-type statistics summary

Real example (summarized) of correct tracking:

```json
{
  "status": "Aceptado",
  "detalles": [
    {
      "tipo": 39,
      "informados": 1,
      "aceptados": 1,
      "rechazados": 0,
      "reparos": 0
    }
  ],
  "detalle_rep_rech": [],
  "xml_resp": "{\"rut_emisor\":\"76387093-6\",\"rut_envia\":\"17084686-9\",\"trackid\":\"25873531\",\"fecha_recepcion\":\"17/12/2025 23:25:30\",\"estado\":\"EPR\",\"estadistica\":[{\"tipo\":39,\"informados\":1,\"aceptados\":1,\"rechazados\":0,\"reparos\":0}],\"detalle_rep_rech\":[]}"
}
```

Notes:

- In the raw SII JSON (`xml_resp`), the **`estado`** field can come as codes (real example: **`EPR`**). It is normal for these codes to vary depending on SII internal processing.
- What matters for a “correct implementation” is: **no HTTP error**, the response is parseable, and the counters in `estadistica` match what you sent.

---

## 8) Common errors (and how they look)

### 8.1 401 Unauthorized / “NO ESTA AUTENTICADO” (tracking)

- **Symptom**: HTTP 401, message like “NO ESTA AUTENTICADO”.
- **Typical cause**: missing/expired token, or the wrong endpoint was called.
- **Mitigation**: pass `SII_TOKEN` (reuse a valid token) or let the test obtain a token using the PFX.

### 8.2 Empty or non-JSON response (tracking) → `JSONDecodeError`

- **Symptom**: JSON parsing error (empty body, HTML, XML, etc.).
- **Typical cause**: upstream problem (auth, endpoint, maintenance), or a non-JSON response.
- **Mitigation**: check HTTP status and body; the test logging already prints endpoint and response.

### 8.3 Code 101 (folio already received)

- **Symptom**: SII rejects indicating the folio was already received.
- **Typical cause**: duplicated folio (not using auto-folio / not persisting state / wrong CAF usage).
- **Mitigation**: use `Folio=0` (auto-folio) + `folio_state.json`, or change CAF/range.

### 8.4 Code 514 (CAF signature invalid)

- **Symptom**: “Firma del CAF Incorrecta”.
- **Typical cause**: CAF was **manually edited** (you changed characters/accents and broke the CAF signature).
- **Mitigation**: re-download the original CAF from SII; do not edit it.

### 8.5 Error 647 (issuance date)

- **Symptom**: rejection related to date (issuance date out of allowed range/period).
- **Mitigation**: this script already **forces `FchEmis` to today** before stamping.

### 8.6 Encoding errors / invalid characters (CAF)

- **Symptom**: XSD validation fails due to strange characters (e.g., U+FFFD / `&#65533;`).
- **Typical cause**: CAF was downloaded/saved with incorrect encoding or got “corrupted” by an editor/viewer (re-encoding on save).
- **Mitigation**: re-download the CAF as a file (do not copy/paste from browser) and **do not open/edit it in text editors**. Treat it as a binary/immutable input and only reference its path.

---

## 9) Operational notes

- **IMPORTANT: DO NOT OPEN THE CAF** in VSCode/Notepad/Word/Excel or any editor/viewer. Even if you “just open it”, it is very common to accidentally save it and change encoding/line-endings, which breaks the CAF signature and later causes SII errors (e.g., 514) or schema/encoding failures.
- **Always treat the CAF as immutable**: download it from SII, store it, and only reference it by path (e.g., `CAF39_PATH` / `facturacion_electronica/Folios/CAF39.xml`).
- **Do not edit the CAF manually** (it invalidates the signature and SII returns error 514).
- If you switch CAF (different range), delete or adjust `facturacion_electronica/out/folio_state.json` to avoid jumps/collisions.
- If you are missing `lxml` or other dependencies, install with `pip install -r requirements.txt`.

---

## 10) Java equivalents (libraries similar to Python dependencies)

If you re-implement this flow in Java, these are common equivalents to the Python libraries used here:

- **HTTP client (`requests`, `urllib3`)**

  - Java: `java.net.http.HttpClient` (JDK 11+) or OkHttp / Apache HttpClient
  - Needed for: `GET` seed, `POST` token, `POST` multipart envío, `GET` tracking

- **XML parsing + XSD validation (`lxml`)**

  - Java: JAXP (`DocumentBuilderFactory`, `SchemaFactory`) + Xerces (often used under the hood)
  - Needed for: building/parsing XML, validating against XSD

- **XML Digital Signature (XMLDSIG) / Canonicalization**

  - Java: Apache Santuario (`org.apache.santuario:xmlsec`) or built-in `javax.xml.crypto.dsig` (may vary by JDK/provider)
  - Needed for: signing seed XML, signing `Documento` and `SetDTE`, canonicalization (C14N)

- **Crypto / Certificates / PKCS#12 (`cryptography`, `pyOpenSSL`)**

  - Java: Bouncy Castle (`bcprov` + `bcpkix`) and/or Java `KeyStore` (`PKCS12`)
  - Needed for: loading `.pfx/.p12`, extracting private key + certificate, RSA-SHA1 signing

- **Timezone utilities (`pytz`)**

  - Java: `java.time` (`ZonedDateTime`, `ZoneId.of(\"America/Santiago\")`)
  - Needed for: `TmstFirmaEnv` / `TmstFirma` and time formatting

- **PDF417 (`pdf417gen`)**

  - Java: ZXing (`com.google.zxing:core`) supports PDF_417 (or other PDF417 encoders)
  - Needed for: generating the barcode image from TED

- **SOAP client (`zeep`)**
  - Java: JAX-WS or Apache CXF
  - Note: this slim repo focuses on boleta+tracking over REST endpoints; SOAP may be used in other DTE flows.
