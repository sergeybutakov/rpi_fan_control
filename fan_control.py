from gpiozero import PWMOutputDevice, DigitalInputDevice
import time
import os

# Настройки
FAN_PIN = 14  # GPIO для синего (PWM)
TACH_PIN = 23  #  # GPIO для зеленого (TACH)
TEMP_ON = 52  # Температура включения вентилятора
TEMP_OFF = 49  # Температура выключения вентилятора
TEMP_HIGH = 75  # Максимальная температура (100% оборотов)
TEMP_MEDIUM = 70  # Пограничная температура, до которой вентилятор использует указанный потенциал (MAX_FAN_SPEED_BELOW) в %
MAX_FAN_SPEED_BELOW = 50  # Потенциал, который используется до пограничной температуры (TEMP_MEDIUM)
COOLDOWN_TIME = 10  # Принудительное время работы вентиляторя на 100%, после достижения максимальной температуры (TEMP_HIGH), в секундах
BLOW_TIME = 3  # Время продувки вентилятора при запуске скрипта (в секундах)
PRE_BLOW_PAUSE = 2  # Время ожидания перед продувкой (BLOW_TIME)
IMPULSES_PER_REVOLUTION = 2  # Импульсы тахометра за один оборот
LOW_TEMP_STABLE_COUNT = 5  # Проверок перед выключением вентилятора
MIN_FAN_SPEED = 0.25  # Минимальная скорость вентилятора для старта

# Инициализация вентилятора
fan = PWMOutputDevice(FAN_PIN, frequency=25)

# Переменные тахометра
rpm_count = 0
last_rpm_time = time.time()
low_temp_counter = 0  # Счетчик стабильного холода

def get_cpu_temperature():
    """Получает температуру процессора."""
    try:
        temp = os.popen("vcgencmd measure_temp").readline().strip()
        return float(temp.replace("temp=", "").replace("'C", ""))
    except ValueError:
        return TEMP_OFF

def map_range(value, in_min, in_max, out_min, out_max):
    """Масштабирование значения."""
    return max(min(out_max, (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min), out_min)

def smooth_start(target_speed, step=0.02, delay=0.1):
    """Плавное изменение скорости вентилятора."""
    current_speed = fan.value
    while abs(current_speed - target_speed) > step:
        current_speed += step if current_speed < target_speed else -step
        fan.value = max(0, min(1, current_speed))
        time.sleep(delay)
    fan.value = target_speed

def notify_change(new_speed, temp, rpm):
    """Вывод информации о скорости вентилятора и RPM."""
    print(f"Температура: {temp:.1f}°C, Скорость: {new_speed * 100:.1f}%, RPM: {rpm}")

def initial_blow():
    """Продувка вентилятора."""
    print(f"Ожидание перед продувкой ({PRE_BLOW_PAUSE} сек)...")
    fan.value = 0
    time.sleep(PRE_BLOW_PAUSE)
    print(f"Запуск продувки ({BLOW_TIME} сек)...")
    fan.value = 1
    time.sleep(BLOW_TIME)
    fan.value = 0
    print("Продувка завершена.")

def count_rpm():
    """Обработчик тахометра."""
    global rpm_count
    rpm_count += 1

def calculate_rpm():
    """Вычисляет RPM вентилятора."""
    global rpm_count, last_rpm_time
    elapsed_time = time.time() - last_rpm_time
    last_rpm_time = time.time()
    rpm = (rpm_count / IMPULSES_PER_REVOLUTION) * (60 / elapsed_time) if elapsed_time > 0 else 0
    rpm_count = 0
    return int(rpm)

# Настройка тахометра
tachometer = DigitalInputDevice(TACH_PIN, pull_up=True)
tachometer.when_activated = count_rpm

try:
    fan_running = False
    last_high_temp_time = None
    cooldown_start_time = None
    fan_speed = 0

    initial_blow()

    while True:
        temp = get_cpu_temperature()
        current_rpm = calculate_rpm()

        if temp < TEMP_OFF:
            low_temp_counter += 1
            if low_temp_counter >= LOW_TEMP_STABLE_COUNT:
                smooth_start(0)
                fan_running = False
                fan_speed = 0
        else:
            low_temp_counter = 0  # Если температура выше, сбрасываем счетчик

        if temp >= TEMP_ON:
            if temp > TEMP_HIGH:
                fan_speed = 1
            elif temp > TEMP_MEDIUM:
                fan_speed = map_range(temp, TEMP_MEDIUM, TEMP_HIGH, 0.8, 1)
            else:
                fan_speed = max(map_range(temp, TEMP_ON, TEMP_MEDIUM, MIN_FAN_SPEED, MAX_FAN_SPEED_BELOW / 100), MIN_FAN_SPEED)

            smooth_start(fan_speed)
            fan_running = True

        if last_high_temp_time and not cooldown_start_time and temp < TEMP_HIGH:
            cooldown_start_time = time.time()
            fan_speed = 1

        if cooldown_start_time and time.time() - cooldown_start_time < COOLDOWN_TIME:
            fan_speed = 1
        else:
            cooldown_start_time = None

        notify_change(fan_speed, temp, current_rpm)

        if fan_running:
            fan.value = fan_speed

        time.sleep(1)

except KeyboardInterrupt:
    print("Остановка программы...")

finally:
    fan.value = 0
    print("Очистка завершена.")
