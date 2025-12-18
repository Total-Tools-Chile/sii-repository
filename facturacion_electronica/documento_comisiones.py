# -*- coding: utf-8 -*-
from facturacion_electronica import clase_util as util
import collections


class DocumentoComisiones(object):

    def __init__(self, vals):
        util.set_from_keys(self, vals)

    @property
    def Glosa(self):
        if not hasattr(self, '_glosa'):
            return False
        return self._glosa

    @Glosa.setter
    def Glosa(self, val):
        self._glosa = val

    @property
    def NroLinCom(self):
        if not hasattr(self, '_nro_lin_com'):
            return []
        return self._nro_lin_com

    @NroLinCom.setter
    def NroLinCom(self, val):
        self._nro_lin_com = val

    @property
    def TasaComision(self):
        if not hasattr(self, '_tasa_comision'):
            return 0
        return round(self._tasa_comision, 2)

    @TasaComision.setter
    def TasaComision(self, val):
        self._tasa_comision = val

    @property
    def TasaIVA(self):
        if not hasattr(self, '_tasa_iva'):
            return 19
        return self._tasa_iva

    @TasaIVA.setter
    def TasaIVA(self, val):
        self._tasa_iva = val

    """
        C (comisión)
        O (otros cargos)
    """
    @property
    def TipoMovim(self):
        if not hasattr(self, '_tipo_movim'):
            return 0
        return self._tipo_movim

    @TipoMovim.setter
    def TipoMovim(self, val):
        self._tipo_movim = val

    @property
    def ValComExe(self):
        if not hasattr(self, '_val_com_exe'):
            return 0
        return self._val_com_exe

    @ValComExe.setter
    def ValComExe(self, val):
        self._val_com_exe = val

    @property
    def ValComIVA(self):
        if not hasattr(self, '_val_com_iva'):
            val_com_iva = self.ValComNeto * (self.TasaIVA / 100.0)
            return util.round0(val_com_iva)
        return self._val_com_iva

    @ValComIVA.setter
    def ValComIVA(self, val):
        self._val_com_iva = val

    @property
    def ValComNeto(self):
        if not hasattr(self, '_val_com_neto'):
            return 0
        return self._val_com_neto

    @ValComNeto.setter
    def ValComNeto(self, val):
        self._val_com_neto = val
