import argostranslate.package

installed_packages = argostranslate.package.get_installed_packages()
for pkg in installed_packages:
    print(f"{pkg.from_code} -> {pkg.to_code} : {pkg.from_name} a {pkg.to_name}")
