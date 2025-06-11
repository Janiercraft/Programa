import sys, os, time, zipfile, shutil, subprocess

def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    tmp = sys.argv[1]
    zip_path = os.path.join(tmp, 'app.zip')

    time.sleep(2)  # espera a que la app cierre

    # Limpiar dist (excepto updater.py y update_temp)
    for item in os.listdir(cwd):
        if item in ('updater.py', os.path.basename(tmp)):
            continue
        path = os.path.join(cwd, item)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except:
            pass

    # Extraer nueva versión
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(cwd)

    # Borrar temp
    shutil.rmtree(tmp, ignore_errors=True)

    # Reiniciar
    exe = os.path.join(cwd, 'Calculadora R.Prestige.exe')
    subprocess.Popen([exe], cwd=cwd)

if __name__ == '__main__':
    main()
