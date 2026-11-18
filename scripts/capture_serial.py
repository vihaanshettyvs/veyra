
import serial
import argparse
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description="VEYRA Serial Data Collector")
parser.add_argument("--port", required=True, help="ESP32 serial port")
parser.add_argument("--baud", type=int, default=921600)
args = parser.parse_args()

data_dir = Path(__file__).resolve().parent.parent / "data"
data_dir.mkdir(exist_ok=True)

filename = datetime.now().strftime("serial_%Y%m%d_%H%M%S.log")
output_file = data_dir / filename

print(f"Connecting to {args.port} at {args.baud} baud...")

try:
    with serial.Serial(args.port, args.baud, timeout=1) as esp, \
         output_file.open("w", encoding="utf-8") as log:

        print(f"Connected! Saving data to: {output_file}")
        print("Press Ctrl+C to stop recording.\n")

        while True:
            raw_line = esp.readline()

            if raw_line:
                line = raw_line.decode("utf-8", errors="replace").strip()
                timestamp = datetime.now().isoformat(timespec="milliseconds")

                log.write(f"{timestamp},{line}\n")
                log.flush()

                print(line)

except KeyboardInterrupt:
    print(f"\nRecording stopped. Data saved to {output_file}")

except serial.SerialException as error:
    print(f"Serial connection error: {error}")
