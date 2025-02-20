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
sudo cp fancontrol.service /lib/systemd/system/fancontrol.service
sudo cp fan_control.py /usr/local/sbin/
sudo chmod 644 /lib/systemd/system/fancontrol.service
sudo chmod +x /usr/local/sbin/fan_control.py
sudo systemctl daemon-reload
sudo systemctl enable fancontrol.service
sudo systemctl start fancontrol.service
```
Удалить
```
sudo systemctl stop fancontrol.service
sudo systemctl disable fancontrol.service
sudo systemctl daemon-reload
sudo rm /usr/local/sbin/fan_control.py
sudo rm /lib/systemd/system/fancontrol.service
```

