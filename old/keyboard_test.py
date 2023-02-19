from pynput.keyboard import Key, Listener

def on_press(key):
    print(key)
    print(key.char == 'a')

listener = Listener(on_press=on_press)
listener.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        break

listener.stop()
