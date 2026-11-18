
import asyncio
from bleak import BleakScanner


async def scan_ble_devices():
    print("\n========== VEYRA BLE SCANNER ==========")
    print("Scanning for nearby Bluetooth devices...")
    print("Scan duration: 10 seconds\n")

    try:
        devices = await BleakScanner.discover(timeout=10)

        if not devices:
            print("No BLE devices found.")
            return

        print(f"Found {len(devices)} BLE device(s):\n")

        for device in devices:
            print(f"Device Name    : {device.name or 'Unknown'}")
            print(f"Device Address : {device.address}")
            print("-" * 40)

    except Exception as error:
        print(f"BLE scanning error: {error}")


if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
