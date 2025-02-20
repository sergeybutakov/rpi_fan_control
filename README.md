# RPi Fan Control
### Функции скрипта
- Автоматическое включение и выключение вентилятора в зависимости от температуры.
- Плавное изменение скорости (без резких скачков).
- Режим продувки при старте (100% на несколько секунд).
- Охлаждение после перегрева (удержание 100% скорости некоторое время при достижения пиковой температуры).
- Возможность ручной регулировки параметров.

### Установка
Установите gpiozero (если не установлена)
```
sudo apt install python3-gpiozero
```
Берем файлы, переходим в каталог
```
git clone https://github.com/sergeybutakov/rpi_fan_control.git
cd rpi_fan_control
```
Установка
```
sudo cp pifancontrol.service /lib/systemd/system/pifancontrol.service
sudo cp fan_control.py /usr/local/sbin/
sudo chmod 644 /lib/systemd/system/pifancontrol.service
sudo chmod +x /usr/local/sbin/fan_control.py
sudo systemctl daemon-reload
sudo systemctl enable pifancontrol.service
sudo systemctl start pifancontrol.service
```
Удалить
```
sudo systemctl stop pifancontrol.service
sudo systemctl disable pifancontrol.service
sudo systemctl daemon-reload
sudo rm /usr/local/sbin/fan_control.py
sudo rm /lib/systemd/system/pifancontrol.service
```

