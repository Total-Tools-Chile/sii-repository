# -*- coding: utf-8 -*-
from facturacion_electronica import clase_util as util


class Recep(object):

    def __init__(self, vals={}):
        util.set_from_keys(self, vals)

    @property
    def CdgSIISucur(self):
        if not hasattr(self, '_cdg_sii_sucur'):
            return False
        return self._cdg_sii_sucur

    @CdgSIISucur.setter
    def CdgSIISucur(self, val):
        self._cdg_sii_sucur = val

    @property
    def CiudadRecep(self):
        if not hasattr(self, '_ciudad_recep') or not self._ciudad_recep:
            return ''
        return self._ciudad_recep[:20]

    @CiudadRecep.setter
    def CiudadRecep(self, val):
        self._ciudad_recep = val

    @property
    def CmnaRecep(self):
        if not hasattr(self, '_cmna_recep'):
            return False
        return self._cmna_recep[:20]

    @CmnaRecep.setter
    def CmnaRecep(self, val):
        self._cmna_recep = val

    @property
    def Contacto(self):
        if not hasattr(self, '_contacto'):
            return False
        return self._contacto

    @Contacto.setter
    def Contacto(self, val):
        self._contacto = val

    @property
    def CorreoRecep(self):
        if not hasattr(self, '_correo_recep'):
            return False
        return self._correo_recep[:80]

    @CorreoRecep.setter
    def CorreoRecep(self, val):
        self._correo_recep = val

    @property
    def DirRecep(self):
        if not hasattr(self, '_dir_recep'):
            return False
        return self._dir_recep[:80]

    @DirRecep.setter
    def DirRecep(self, val):
        self._dir_recep = val

    @property
    def GiroRecep(self):
        if not hasattr(self, '_giro_recep'):
            return False
        return self._giro_recep[:40]

    @GiroRecep.setter
    def GiroRecep(self, val):
        self._giro_recep = val

    @property
    def RznSocRecep(self):
        if not hasattr(self, '_rzn_soc_recep'):
            return "Usuario Anonimo"
        return self._rzn_soc_recep[:100]

    @RznSocRecep.setter
    def RznSocRecep(self, val):
        self._rzn_soc_recep = val

    @property
    def RUTRecep(self):
        if not hasattr(self, '_rut_recep'):
            return '66666666-6'
        return self._rut_recep[:10]

    @RUTRecep.setter
    def RUTRecep(self, val):
        self._rut_recep = util.formatear_rut(val)

    @property
    def Nacionalidad(self):
        if not hasattr(self, '_nacionalidad'):
            return False
        return self._nacionalidad

    @Nacionalidad.setter
    def Nacionalidad(self, val):
        self._nacionalidad = val
