# coding=utf-8
__author__ = 'oscar.salvador'

# Agregamos la ruta de los ayudantes de depuración
import sys
sys.path[0:0] = [
  '/home/oscar/.pycharm_helpers/pydev',
  ]

# Para conectar con la depuración remota de PyCharm
import pydevd
pydevd.settrace('10.10.1.69', port=6969, stdoutToServer=True, stderrToServer=True)

# Llamamos a Odoo
execfile('../bin/start_openerp')