# -*- coding: utf-8 -*-
from facturacion_electronica import clase_util as util


class LineaImpuesto(object):
    tax_id = None
    _base = 0
    _base_otr_mnda = 0

    def __init__(self, vals):
        util.set_from_keys(vals, priorizar=['moneda_decimales'])
        self.tax_id = vals['tax_id']
        self._compute_tax()

    @property
    def ActivoFijo(self):
        if not hasattr(self, '_activo_fijo'):
            return False
        return self._activo_fijo

    @ActivoFijo.setter
    def ActivoFijo(self, val):
        self._activo_fijo = val

    @property
    def base(self):
        if self.tax_id and self.tax_id.price_include and self.tax_id.TasaImp != 0:
            return self._base / (1 + (self.tax_id.TasaImp / 100.0))
        return self._base

    @base.setter
    def base(self, val):
        self._base = util.round0(val)

    @property
    def base_otr_mnda(self):
        if self.tax_id and self.tax_id.price_include and self.tax_id.TasaImp != 0:
            return self._base_otr_mnda / (1 + (self.tax_id.TasaImp / 100.0))
        return self._base_otr_mnda

    @base_otr_mnda.setter
    def base_otr_mnda(self, val):
        self._base_otr_mnda = util.round0(val)

    @property
    def cantidad(self):
        if not hasattr(self, '_cantidad'):
            return 0
        return self._cantidad

    @cantidad.setter
    def cantidad(self, val):
        self._cantidad = val

    @property
    def CredEC(self):
        if not hasattr(self, '_credec'):
            if self.tax_id.CredEC:
                return self.MontoImp * (self.tax_id.CredEC / 100.0)
            return 0.0
        return self._credec

    @CredEC.setter
    def CredEC(self, val):
        self._credec = float(val)

    @property
    def moneda_decimales(self):
        if not hasattr(self, '_moneda_decimales'):
            return 0
        self._moneda_decimales

    @moneda_decimales.setter
    def moneda_decimales(self, val):
        self._moneda_decimales = 0

    @property
    def MontoImp(self):
        if not hasattr(self, '_monto_imp'):
            return 0
        return self._monto_imp

    @MontoImp.setter
    def MontoImp(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._monto_imp = mnt

    @property
    def MontoNoReten(self):
        if not hasattr(self, '_monto_no_reten'):
            return 0
        return self._monto_no_reten

    @MontoNoReten.setter
    def MontoNoReten(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._monto_no_reten = mnt

    @property
    def MontoNoRetenOtrMnda(self):
        if not hasattr(self, '_monto_no_reten_otr_mnda'):
            return 0
        return self._monto_no_reten_otr_mnda

    @MontoNoRetenOtrMnda.setter
    def MontoNoRetenOtrMnda(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._monto_no_reten_otr_mnda = mnt

    @property
    def MontoReten(self):
        if not hasattr(self, '_monto_reten'):
            return 0
        return self._monto_reten

    @MontoReten.setter
    def MontoReten(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._monto_reten = mnt

    @property
    def MontoRetenOtrMnda(self):
        if not hasattr(self, '_monto_reten_otr_mnda'):
            return 0
        return self._monto_reten_otr_mnda

    @MontoRetenOtrMnda.setter
    def MontoRetenOtrMnda(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._monto_reten_otr_mnda = mnt

    @property
    def VlrImpOtrMnda(self):
        if not hasattr(self, '_vlr_imp_otr_mnda'):
            return 0
        return self._vlr_imp_otr_mnda

    @VlrImpOtrMnda.setter
    def VlrImpOtrMnda(self, val):
        if self.moneda_decimales == 0:
            mnt = util.round0(val)
        else:
            mnt = round(val, self.moneda_decimales)
        self._vlr_imp_otr_mnda = mnt

    def monto_fijo(self):
        return self.tax_id.TasaImp * self.cantidad

    def _compute_tax(self):
        if self.tax_id.especifico:
            monto = self.monto_fijo()
        else:
            if not self.tax_id:
                return 0.0
            elif self.tax_id.TasaImp == 0:
                monto = self.base
            else:
                monto = (self.base * (self.tax_id.TasaImp / 100.0))
        self.MontoImp = monto
        if self.tax_id.Retencion:
            self.MontoReten = (self.base * (self.tax_id.Retencion / 100.0))
            self.MontoNoRet = self.MontoImp - self.MontoReten
        if self.base_otr_mnda:
            monto = 0
            if self.tax_id.TasaImpOtrMnda == 0:
                monto = self.base_otr_mnda
            else:
                monto = (self.base_otr_mnda * (self.tax_id.TasaImpOtrMnda / 100.0))
            self.VlrImpOtrMnda = monto
            if self.tax_id.Retencion:
                self.MontoRetenOtrMnda = (self.base_otr_mnda * (self.tax_id.Retencion / 100.0))
                self.MontoNoRetenOtrMnda = self.VlrImpOtrMnda - self.MontoRetenOtrMnda

    def get_tax_monto(self, moneda_decimales=0):
        self._compute_tax()
        return self.MontoImp
