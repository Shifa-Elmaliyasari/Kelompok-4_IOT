
import serial
import sqlite3
import re
from datetime import datetime

# Sesuaikan port COM-mu
SERIAL_PORT = "COM7"  # Windows: COM3, COM4 | Linux/Mac: /dev/ttyUSB0
BAUD_RATE   = 115200
DB_PATH     = r"D:\Kuliah\DOC\Semester 6\IOT\TUGAS\Tugas Kelompok\Projek UAS\room_monitor_esp32\sensor_data.db"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity    REAL,
            lux         REAL,
            sound_level INTEGER,
            gas_raw     INTEGER,
            gas_ppm     REAL,
            motion      INTEGER
        )
    """)
    conn.commit()

def parse_line(line):
    """
    Parsing output serial: 
    "28.5°C | 65.2% | 342.0 lux | 1820 level | Gas:430 (~105ppm) | Gerak:-"
    """
    pattern = r"([\d.]+)°C \| ([\d.]+)% \| ([\d.]+) lux \| (\d+) level \| Gas:(\d+) \(~([\d.]+)ppm\) \| Gerak:(\S+)"
    match = re.search(pattern, line)
    if match:
        return {
            "temperature": float(match.group(1)),
            "humidity":    float(match.group(2)),
            "lux":         float(match.group(3)),
            "sound_level": int(match.group(4)),
            "gas_raw":     int(match.group(5)),
            "gas_ppm":     float(match.group(6)),
            "motion":      1 if match.group(7) == "TERDETEKSI" else 0
        }
    return None

def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    print(f"Terhubung ke {DB_PATH}, menunggu data dari {SERIAL_PORT}...")

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
        while True:
            try:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {raw}")
                data = parse_line(raw)
                if data:
                    conn.execute("""
                        INSERT INTO sensor_readings
                        (temperature, humidity, lux, sound_level, gas_raw, gas_ppm, motion)
                        VALUES (:temperature, :humidity, :lux, :sound_level, :gas_raw, :gas_ppm, :motion)
                    """, data)
                    conn.commit()
            except KeyboardInterrupt:
                print("\nDihentikan.")
                break
    conn.close()

if __name__ == "__main__":
    main()