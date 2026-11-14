import tkinter as tk
import threading
import time
import evdev
from evdev import ecodes
from collections import deque

class CPSLimiterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPS Limiter & Sensitivity")
        self.root.geometry("300x380")
        self.root.attributes("-topmost", True)

        self.is_running = False
        self.left_limit = 12
        self.right_limit = 12
        self.sensitivity = 0.61
        self.left_clicks = deque()
        self.right_clicks = deque()

        tk.Label(root, text="Mouse Sensitivity (e.g., 0.61):").pack(pady=5)
        self.sens_entry = tk.Entry(root)
        self.sens_entry.insert(0, "0.61")
        self.sens_entry.pack()

        tk.Label(root, text="Left Click Limit (CPS):").pack(pady=5)
        self.left_entry = tk.Entry(root)
        self.left_entry.insert(0, "12")
        self.left_entry.pack()

        tk.Label(root, text="Right Click Limit (CPS):").pack(pady=5)
        self.right_entry = tk.Entry(root)
        self.right_entry.insert(0, "12")
        self.right_entry.pack()

        self.toggle_btn = tk.Button(root, text="START (OFF)", bg="red", fg="white", font=("Arial", 12, "bold"), command=self.toggle_state)
        self.toggle_btn.pack(pady=20)

        self.mouse_device = self.find_mouse()
        self.ui = None

    def find_mouse(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        mouse_device = None

        print("\n--- Scanned Devices ---")
        for device in devices:
            caps = device.capabilities()
            if ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]:
                if ecodes.EV_REL in caps:
                    print(f"-> MOUSE FOUND: {device.name} ({device.path})")
                    if not mouse_device:
                        mouse_device = device
                else:
                    print(f"-> Keyboard/Extra Keys: {device.name}")
            else:
                print(f"-> Other Device: {device.name}")

        return mouse_device

    def toggle_state(self):
        if not self.mouse_device:
            print("ERROR: Compatible mouse device not found!")
            self.toggle_btn.config(text="ERROR: MOUSE NOT FOUND", bg="orange")
            return

        self.is_running = not self.is_running
        if self.is_running:
            try:
                self.left_limit = int(self.left_entry.get())
                self.right_limit = int(self.right_entry.get())
                self.sensitivity = float(self.sens_entry.get())
            except ValueError:
                self.left_limit = 12
                self.right_limit = 12
                self.sensitivity = 0.61

            self.toggle_btn.config(text="STOP (ON)", bg="green")
            self.left_clicks.clear()
            self.right_clicks.clear()

            threading.Thread(target=self.listen_mouse, daemon=True).start()
        else:
            self.toggle_btn.config(text="START (OFF)", bg="red")
            if self.ui:
                try:
                    self.ui.close()
                except:
                    pass
                self.ui = None
            try:
                self.mouse_device.ungrab()
            except:
                pass

    def listen_mouse(self):
        try:
            self.mouse_device.grab()
            self.ui = evdev.UInput.from_device(self.mouse_device, name="CPS-Limiter-Virtual-Mouse")

            # Accumulators for smooth sensitivity
            acc_x = 0.0
            acc_y = 0.0

            for event in self.mouse_device.read_loop():
                if not self.is_running:
                    break

                current_time = time.time()

                # --- SENSITIVITY (Mouse Movement) ---
                if event.type == ecodes.EV_REL:
                    if event.code == ecodes.REL_X:
                        acc_x += (event.value * self.sensitivity)
                        int_move = int(acc_x)
                        acc_x -= int_move
                        if int_move != 0 and self.ui:
                            self.ui.write(event.type, event.code, int_move)
                            self.ui.syn()
                    elif event.code == ecodes.REL_Y:
                        acc_y += (event.value * self.sensitivity)
                        int_move = int(acc_y)
                        acc_y -= int_move
                        if int_move != 0 and self.ui:
                            self.ui.write(event.type, event.code, int_move)
                            self.ui.syn()
                    else:
                        # Scroll wheel etc.
                        if self.ui:
                            self.ui.write(event.type, event.code, event.value)
                            self.ui.syn()

                # --- CPS LIMITER (Clicks) ---
                elif event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_LEFT:
                        if event.value == 1:
                            while self.left_clicks and current_time - self.left_clicks[0] > 1.0:
                                self.left_clicks.popleft()
                            if len(self.left_clicks) >= self.left_limit:
                                continue
                            self.left_clicks.append(current_time)

                    elif event.code == ecodes.BTN_RIGHT:
                        if event.value == 1:
                            while self.right_clicks and current_time - self.right_clicks[0] > 1.0:
                                self.right_clicks.popleft()
                            if len(self.right_clicks) >= self.right_limit:
                                continue
                            self.right_clicks.append(current_time)

                    # Forward the click event to the virtual mouse
                    if self.ui:
                        self.ui.write(event.type, event.code, event.value)
                        self.ui.syn()

                else:
                    # Forward other events (like SYNC)
                    if self.ui:
                        self.ui.write(event.type, event.code, event.value)
                        self.ui.syn()

        except Exception as e:
            print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CPSLimiterApp(root)
    root.mainloop()
