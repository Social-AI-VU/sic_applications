from sic_framework.devices import Nao


def test_func(a):
    print("Pressed", a.value)


nao = Nao(ip="192.168.178.45")
nao.buttons.register_callback(test_func)

while True:
    pass  # Keep script alive
