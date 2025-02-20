from gpiozero import PWMOutputDevice
import time
import os

# Настройки
FAN_PIN = 14  # Номер GPIO
TEMP_LOW = 50  # Температура, ниже которой вентилятор выключается
TEMP_HIGH = 75  # Температура предела, выше которой вентилятор работает на 100%
TEMP_MEDIUM = 70  # Температура, до которой вентилятор может использовать до 80% мощности
MAX_FAN_SPEED_BELOW_70 = 70  # Максимальная скорость вентилятора до 70°C
COOLDOWN_TIME = 10  # Время удержания вентилятора на 100% после перегрева (в секундах)
BLOW_TIME = 4  # Время продувки вентилятора при запуске (в секундах)
PRE_BLOW_PAUSE = 2  # Время ожидания перед продувкой

# Инициализация вентилятора через gpiozero
fan = PWMOutputDevice(FAN_PIN, frequency=25)

def get_cpu_temperature():
    """Получает температуру процессора."""
    try:
        temp = os.popen("vcgencmd measure_temp").readline().strip()
        return float(temp.replace("temp=", "").replace("'C", ""))
    except ValueError:
        return TEMP_LOW  # Возвращаем безопасное значение

def map_range(value, in_min, in_max, out_min, out_max):
    """Масштабирование значения из одного диапазона в другой."""
    return max(min(out_max, (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min), out_min)

def smooth_start(target_speed, step=0.02, delay=0.1):
    """Плавное изменение скорости вентилятора."""
    current_speed = fan.value  # Текущее значение PWM (от 0 до 1)
    while abs(current_speed - target_speed) > step:
        current_speed += step if current_speed < target_speed else -step
        fan.value = max(0, min(1, current_speed))  # Устанавливаем значение в пределах [0,1]
        time.sleep(delay)
    fan.value = target_speed  # Устанавливаем точное значение в конце

def notify_change(new_speed, temp):
    """Вывод информации о скорости вентилятора."""
    print(f"Температура: {temp:.1f}°C, Скорость вентилятора: {new_speed * 100:.1f}%")

def initial_blow():
    """Продувка вентилятора при запуске с паузой перед стартом."""
    print(f"Ожидание перед продувкой ({PRE_BLOW_PAUSE} сек)...")
    fan.value = 0  # Выключаем вентилятор перед продувкой
    time.sleep(PRE_BLOW_PAUSE)

    print(f"Запуск продувки ({BLOW_TIME} сек)...")
    fan.value = 1  # 100% мощности
    time.sleep(BLOW_TIME)
    fan.value = 0  # Остановить вентилятор
    print("Продувка завершена.")

try:
    fan_running = False
    last_high_temp_time = None
    cooldown_start_time = None
    fan_speed = 0  # Инициализируем fan_speed перед циклом

    initial_blow()  # Продувка вентилятора

    while True:
        temp = get_cpu_temperature()

        if temp < TEMP_LOW:
            fan.value = 0  # Выключаем вентилятор
            fan_running = False
            fan_speed = 0  # Устанавливаем fan_speed в 0
        elif temp > TEMP_HIGH:
            smooth_start(1)  # Запускаем вентилятор на 100%
            fan_running = True
            last_high_temp_time = time.time()
            cooldown_start_time = None
            fan_speed = 1  # 100%
        elif temp > TEMP_MEDIUM:
            fan_speed = map_range(temp, TEMP_MEDIUM, TEMP_HIGH, 0.8, 1)  # 80% - 100%
        else:
            fan_speed = map_range(temp, TEMP_LOW, TEMP_MEDIUM, 0.2, MAX_FAN_SPEED_BELOW_70 / 100)  # 20% - MAX

        # Если температура была выше предельной и снижается, удерживаем вентилятор на 100% еще указанное время
        if last_high_temp_time and not cooldown_start_time and temp < TEMP_HIGH:
            cooldown_start_time = time.time()
            fan_speed = 1  # Держим вентилятор на 100%

        # Проверка для удержания вентилятора на максимальной скорости в течение заданного времени
        if cooldown_start_time and time.time() - cooldown_start_time < COOLDOWN_TIME:
            fan_speed = 1  # 100% во время охлаждения

        notify_change(fan_speed, temp)

        if not fan_running:
            smooth_start(fan_speed)
            fan_running = True
        else:
            fan.value = fan_speed  # Обычное обновление скорости

        time.sleep(1)  # Интервал обновления

except KeyboardInterrupt:
    print("Остановка программы...")

finally:
    fan.value = 0  # Останавливаем вентилятор
    print("Очистка завершена.")
