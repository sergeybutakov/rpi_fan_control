from gpiozero import PWMOutputDevice, DigitalInputDevice
import time
import os

# Настройки
FAN_PIN = 14  # GPIO для синего (PWM)
TACH_PIN = 23  # GPIO для зеленого (TACH)
TEMP_LOW = 50  # Минимальная температура, бездействие вентилятора
TEMP_HIGH = 75  # Максимальная температура, 100% потенциал вентилятора
TEMP_MEDIUM = 70  # Пограничная температура, до которой вентилятор использует указанный потенциал (MAX_FAN_SPEED_BELOW) в %
MAX_FAN_SPEED_BELOW = 50  # Потенциал, который используется до пограничной температуры (TEMP_MEDIUM)
COOLDOWN_TIME = 10  # Принудительное время работы вентилятора на 100%, после достижения максимальной температуры
BLOW_TIME = 4  # Время продувки вентилятора при запуске
PRE_BLOW_PAUSE = 2  # Время ожидания перед продувкой
STARTUP_DELAY = 7  # Время ожидания перед запуском вентилятора в режиме бездействия

IMPULSES_PER_REVOLUTION = 2  # Количество импульсов тахометра за один оборот

# Инициализация вентилятора через gpiozero
fan = PWMOutputDevice(FAN_PIN, frequency=25)

# Переменные для тахометра
rpm_count = 0
last_rpm_time = time.time()

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

def notify_change(new_speed, temp, rpm):
    """Вывод информации о скорости вентилятора и RPM."""
    print(f"Температура: {temp:.1f}°C, Скорость вентилятора: {new_speed * 100:.1f}%, RPM: {rpm}")

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

def count_rpm():
    """Обработчик прерывания для подсчета оборотов вентилятора."""
    global rpm_count
    rpm_count += 1

def calculate_rpm():
    """Вычисляет текущие обороты вентилятора."""
    global rpm_count, last_rpm_time
    elapsed_time = time.time() - last_rpm_time
    last_rpm_time = time.time()
    
    if elapsed_time > 0:
        rpm = (rpm_count / IMPULSES_PER_REVOLUTION) * (60 / elapsed_time)
    else:
        rpm = 0

    rpm_count = 0  # Сбрасываем счетчик
    return int(rpm)

# Настройка тахометра через gpiozero
tachometer = DigitalInputDevice(TACH_PIN, pull_up=True)
tachometer.when_activated = count_rpm

try:
    fan_running = False
    last_high_temp_time = None
    cooldown_start_time = None
    startup_delay_start = None
    fan_speed = 0  # Инициализируем fan_speed перед циклом

    initial_blow()  # Продувка вентилятора

    while True:
        temp = get_cpu_temperature()
        current_rpm = calculate_rpm()

        if temp < TEMP_LOW:
            fan.value = 0  # Выключаем вентилятор
            fan_running = False
            fan_speed = 0  # Устанавливаем fan_speed в 0
            startup_delay_start = None  # Сбрасываем таймер задержки

        elif temp >= TEMP_LOW:
            if not fan_running and startup_delay_start is None:
                startup_delay_start = time.time()  # Запоминаем момент, когда температура превысила 50°C

            # Если температура держится выше 50°C стабильно, включаем вентилятор
            if startup_delay_start and time.time() - startup_delay_start >= STARTUP_DELAY:
                if temp > TEMP_HIGH:
                    fan_speed = 1  # 100%
                elif temp > TEMP_MEDIUM:
                    fan_speed = map_range(temp, TEMP_MEDIUM, TEMP_HIGH, 0.8, 1)  # 80% - 100%
                else:
                    fan_speed = map_range(temp, TEMP_LOW, TEMP_MEDIUM, 0.2, MAX_FAN_SPEED_BELOW / 100)  # 20% - MAX

                smooth_start(fan_speed)
                fan_running = True  # Теперь вентилятор работает

        # Если температура была выше предельной и снижается, удерживаем вентилятор на 100% еще указанное время
        if last_high_temp_time and not cooldown_start_time and temp < TEMP_HIGH:
            cooldown_start_time = time.time()
            fan_speed = 1  # Держим вентилятор на 100%

        # Проверка для удержания вентилятора на максимальной скорости в течение заданного времени
        if cooldown_start_time and time.time() - cooldown_start_time < COOLDOWN_TIME:
            fan_speed = 1  # 100% во время охлаждения
        else:
            cooldown_start_time = None  # Сбрасываем таймер, если время истекло

        notify_change(fan_speed, temp, current_rpm)

        if fan_running:
            fan.value = fan_speed  # Обычное обновление скорости

        time.sleep(1)  # Интервал обновления

except KeyboardInterrupt:
    print("Остановка программы...")

finally:
    fan.value = 0  # Останавливаем вентилятор
    print("Очистка завершена.")
