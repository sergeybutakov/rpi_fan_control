# RPi Fan Control
Скрипт управления pwm вентилятором для raspberry pi, через gpio, используя gpiozero, на примере noctua nf a4x10 pwm 5v. Вы можете использовать любой другой pwm вентилятор 5v, главное чтобы напряжение на pwm проводе было ниже 3.3v - есть большой риск поджечь Raspberry Pi.
Для подключения нужно переделать разъем 4 pin в dupont, я использовал доп разъемы в комплекте с noctua, чтобы не портить провод вентилятора. 

### Функции
- Продувка вентилятора перед запуском скрипта. Выполняется на 100% мощности, столько секунд, сколько вы захотите.
- Плавное старт и любые изменения скорости вентилятора, во избежании излишних колебаний и скачков.
- Пограничная температура 70 градусов, до которой используется 50% мощности вентилятора. После 70 градусов, вентелятор может продолжить использовать потенциал без ограничений. Это сделает его тише в повседневных задачах, но если будут серьезные нагрузки примет полноценное участие. НО это не означает, что при температуре 72 градуса мощность вентилятора будет 100% - алгоритм просто удерживает потенциал до необходимого случая.
- При снижении температуры, после достигнутых 75 градусов, будет работать принудительное охлаждение с мощностью вентилятора в 100% на протяжении 10 секунд.

### Доступные настройки
```
FAN_PIN = 14  # GPIO для синего (PWM)
TACH_PIN = 23  # GPIO для зеленого (TACH)
TEMP_LOW = 50  # Минимальная температура, бездействие вентилятора
TEMP_HIGH = 75  # Максимальная температура, 100% потенциал вентилятора
TEMP_MEDIUM = 70  # Пограничная температура, до которой вентилятор использует указанный потенциал (MAX_FAN_SPEED_BELOW) в %
MAX_FAN_SPEED_BELOW = 50  # Потенциал, который используется до пограничной температуры (TEMP_MEDIUM)
COOLDOWN_TIME = 10  # Принудительное время работы вентиляторя на 100%, после достижения максимальной температуры (TEMP_HIGH), в секундах
BLOW_TIME = 4  # Время продувки вентилятора при запуске скрипта (в секундах)
PRE_BLOW_PAUSE = 2  # Время ожидания перед продувкой (BLOW_TIME)
STARTUP_DELAY = 7  # Время ожидания перед запуском вентилятора в режиме бездействия (TEMP_LOW), в секундах
```

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

