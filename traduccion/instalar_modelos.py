import argostranslate.package
import argostranslate.translate

# Actualiza el índice de paquetes disponibles
argostranslate.package.update_package_index()

# Idiomas origen y destino
from_code = "es"
to_code = "fr"

# Busca el paquete de traducción
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(
    (p for p in available_packages if p.from_code == from_code and p.to_code == to_code),
    None
)

if package_to_install:
    print(f"Descargando paquete {from_code} -> {to_code}...")
    path = package_to_install.download()
    print(f"Instalando paquete desde {path}...")
    argostranslate.package.install_from_path(path)
    print("Instalación completada.")
else:
    print(f"No se encontró paquete para {from_code} -> {to_code}")
