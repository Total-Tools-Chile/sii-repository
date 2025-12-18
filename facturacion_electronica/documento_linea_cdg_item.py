# -*- coding: utf-8 -*-
from facturacion_electronica import clase_util as util
import collections


class LineaDetalleCdgItem(object):

    def __init__(self, vals):
        util.set_from_keys(self, vals)

    @property
    def TpoCodigo(self):
        if not hasattr(self, '_tpo_codigo'):
            return []
        return self._tpo_codigo

    @TpoCodigo.setter
    def TpoCodigo(self, val):
        self._tpo_codigo = val

    @property
    def VlrCodigo(self):
        if not hasattr(self, '_vlr_codigo'):
            return 'INT1'
        return self._vlr_codigo

    @VlrCodigo.setter
    def VlrCodigo(self, val):
        self._vlr_codigo = val
