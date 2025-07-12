"""
This script demonstrates how to use the Nao buttons.
"""

from sic_framework.devices import Nao

def test_func(a):
    print("Pressed: ", a.value)


nao = Nao(ip="XXX")
nao.buttons.register_callback(test_func)

while True:
    pass  # Keep script alive