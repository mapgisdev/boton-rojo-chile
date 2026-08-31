# Instalación de las unidades systemd

```bash
sudo useradd --system --home /opt/boton-rojo --shell /usr/sbin/nologin botonrojo
sudo install -d -o botonrojo -g botonrojo /datos/{gfs,productos,cog,estaticos}
sudo install -d -m 750 -o root -g botonrojo /etc/boton-rojo

sudo cp boton-rojo-*.service boton-rojo.target boton-rojo.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now boton-rojo.timer
```

## Comprobar

```bash
systemctl list-timers boton-rojo.timer      # próxima ejecución
systemctl start boton-rojo.target           # corrida manual, ahora
journalctl -u 'boton-rojo-*' -f             # registro en vivo de las tres etapas
systemctl status boton-rojo-calculo.service # resultado de la última corrida
```

## Por qué systemd y no Airflow

Son cinco unidades de texto plano, versionables en git, con reintentos, límites de
CPU y memoria, aislamiento del sistema de archivos y registro centralizado — sin
base de datos de metadatos, sin planificador, sin interfaz web que parchear. Airflow 3
se justifica cuando el flujo se ramifique, haga falta reprocesar el pasado, o lo
opere más de una persona. Antes de eso es infraestructura que hay que mantener sin
que resuelva un problema que se tenga.
