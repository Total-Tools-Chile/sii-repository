# -*- coding: utf-8 -*-
import base64
import json
import os
from lxml import etree


class UserError(Exception):
    """Clase perdida"""
    pass


class Warning(Exception):
    """Clase perdida"""
    pass


class Caf(object):

    def __init__(self, cafList):
        """Recibe lista de caf strings en base64,
        decodifica y guarda."""
        self.decodedCafs = []
        for caf in cafList:
            decodedCaf = base64.b64decode(caf).decode('ISO-8859-1')
            self.decodedCafs.append(decodedCaf)

    def _state_path(self):
        """
        Archivo local para persistir el último folio usado por (RUTEmisor, TipoDTE).
        Se puede sobreescribir con env var FOLIO_STATE_PATH.
        """
        env_path = os.environ.get("FOLIO_STATE_PATH")
        if env_path:
            return env_path
        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "out")
        os.makedirs(out_dir, exist_ok=True)
        return os.path.join(out_dir, "folio_state.json")

    def _load_state(self, path):
        try:
            if not os.path.exists(path):
                return {}
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_state(self, path, state):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, path)

    def _caf_ranges(self, TipoDTE):
        """
        Retorna lista de rangos disponibles para el TipoDTE en los CAF cargados:
        [(rut_emisor, d, h, xml_tree), ...]
        """
        ranges = []
        for decodedCaf in self.decodedCafs:
            post = etree.XML(decodedCaf)
            try:
                td = int(post.find('CAF/DA/TD').text)
            except Exception:
                td = None
            if td != int(TipoDTE):
                continue
            rut_emisor = (post.find('CAF/DA/RE').text or "").strip()
            d = int(post.find('CAF/DA/RNG/D').text)
            h = int(post.find('CAF/DA/RNG/H').text)
            ranges.append((rut_emisor, d, h, post))
        return ranges

    def next_folio(self, TipoDTE, rut_emisor=None, state_path=None):
        """
        Devuelve el siguiente folio (incremental +1) dentro del rango del CAF.
        - Solo usa CAF cuyo TD coincida con TipoDTE.
        - Persiste el último folio usado en un JSON local, para no repetir folios.
        """
        ranges = self._caf_ranges(TipoDTE)
        if not ranges:
            raise UserError(f"No hay CAF cargado para TipoDTE {TipoDTE}")

        # Si se pasa rut_emisor, preferimos el CAF del mismo RUT.
        if rut_emisor:
            rut_emisor = rut_emisor.strip()
            filtered = [r for r in ranges if r[0] == rut_emisor]
            if filtered:
                ranges = filtered

        # Elegimos el primer rango (en la práctica suele venir 1 CAF por tipo).
        caf_rut, d, h, _post = ranges[0]
        key_rut = rut_emisor or caf_rut
        if not key_rut:
            key_rut = caf_rut or "SIN_RUT"
        state_path = state_path or self._state_path()
        state = self._load_state(state_path)
        key = f"{key_rut}|{int(TipoDTE)}"
        last = int(state.get(key, d - 1))
        nxt = max(d, last + 1)
        if nxt > h:
            raise UserError(
                f"Sin folios disponibles para {key_rut} TipoDTE {TipoDTE}. "
                f"Rango CAF: {d}-{h}. Último usado: {last}. Solicita un nuevo CAF."
            )
        state[key] = nxt
        self._save_state(state_path, state)
        return nxt

    def get_caf_file(self, folio, TipoDTE):
        """Esta función es llamada desde dte"""
        if not self.decodedCafs:
            raise UserError('There is no CAF file available or in use ' +
                            'for this Document. Please enable one.')
        for decodedCaf in self.decodedCafs:
            post = etree.XML(decodedCaf)
            folio_inicial = post.find('CAF/DA/RNG/D').text
            folio_final = post.find('CAF/DA/RNG/H').text
            if folio in range(int(folio_inicial), (int(folio_final)+1)):
                return post
        if folio > int(folio_final):
            msg = '''El folio de este documento: {} está fuera de rango \
del CAF vigente (desde {} hasta {}). Solicite un nuevo CAF en el sitio \
www.sii.cl'''.format(folio, folio_inicial, folio_final)
            raise UserError(msg)
        raise UserError('No Existe Caf para %s folio %s' % (TipoDTE, folio))
