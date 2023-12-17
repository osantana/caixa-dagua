import time
import network
import machine

import ili9341
from xglcd_font import XglcdFont


DEFAULT_HC12_SET_PIN = 21

UART_0 = 0
UART_0_TX_GPIO_PIN = 1
UART_0_RX_GPIO_PIN = 3
UART_0_BAUD = 9600

DISPLAY_CS_PIN = 16
DISPLAY_DC_PIN = 4
DISPLAY_RST_PIN = 17
DISPLAY_SCK_PIN = 14
DISPLAY_MOSI_PIN = 13
DISPLAY_BAUDRATE = 40000000  # Baud rate of 40000000 seems about the max

DEFAULT_HC12_SET_PIN = 21


WHITE = ili9341.color565(255, 255, 255)
GRAY = ili9341.color565(210, 210, 210)
BLACK = ili9341.color565(0, 0, 0)
BLUE = ili9341.color565(0, 0, 255)
RED = ili9341.color565(255, 0, 0)


def _setup_display():
    cs_pin = machine.Pin(DISPLAY_CS_PIN)
    dc_pin = machine.Pin(DISPLAY_DC_PIN)
    rst_pin = machine.Pin(DISPLAY_RST_PIN)
    spi = machine.SPI(1,
        baudrate=DISPLAY_BAUDRATE,
        sck=machine.Pin(DISPLAY_SCK_PIN),
        mosi=machine.Pin(DISPLAY_MOSI_PIN),
    )

    return ili9341.Display(spi, dc=dc_pin, cs=cs_pin, rst=rst_pin, rotation=90, width=320, height=240)


class NetworkError(Exception):
    pass


class MissingConfiguration(Exception):
    pass


class NetworkInterface:
    def __init__(self, wlan=None, hostname="caixa-dagua"):
        if wlan is None:
            wlan = network.WLAN(network.STA_IF)
            
        self.wlan = wlan
        self.activate()

    @property
    def connected(self):
        return self.wlan.isconnected()
    
    def activate(self):
        return self.wlan.active(True)
        
    def deactivate(self):
        return self.wlan.active(False)
    
    def config(self, **configs):
        if not configs:
            return
        
        configs.pop("hostname" )
        if not configs:
            return
        
        return self.wlan.config(**configs)
    
    def connect(self, ssid, key, **configs):
        self.activate()
        self.config(**configs)
        
        conn = self.wlan.connect(ssid, key)
        while not self.connected:
            pass
        return conn

    def ipconfig(self):
        ip, netmask, gateway, dns = self.wlan.ifconfig()
        mac = self.wlan.config("mac")
        return {
            "ip": ip,
            "netmask": netmask,
            "gateway": gateway,
            "dns": dns,
            "mac": ":".join(f"{x:x}" for x in mac),
        }

    def scan(self, timeout=3):
        count = 0
        while count < timeout:
            aps = self.wlan.scan()
            time.sleep(1)
            count += 1
        return aps


class Radio:
#     def __init__(self, uart=None, set_pin=DEFAULT_HC12_SET_PIN):
#         if uart is None:
#             uart = machine.UART(UART_0, baudrate=UART_0_BAUD, rx=UART_0_RX_GPIO_PIN, tx=UART_0_TX_GPIO_PIN)
#         self.uart = uart
#         self.set_pin = set_pin
#         
    def send(self, message):
        pass


class Configuration:
    def __init__(self):
        self.initial_clock = "2024-01-01 00:00:00"

        # TODO: choose network and save it.
        self.ssid = "genius"
        self.password = "deadbeef01"
        self.mode = "dhcp"
        self.ip = ""
        self.netmask = ""
        self.default_gw = ""
        self.dns = ""
        
    def save(self):
        # TODO: save it to non-volatile memory
        pass
    
    def load(self):
        # TODO: read it from non-volatile memory
        raise MissingConfiguration()
    
    @classmethod
    def setup(cls, clock, interface):
        config = cls()
        
        if config.load():
            return config
        
        # setup clock: year-month-day hour:minute:second
        # 2024-01-01 00:00:00
        # up/down=increment/decrement left/right=navigate select=enter rst=back
        #
        # setup network: wifi: ssid/password ip: dhcp/manual manual: ip/netmask/router/dns
        # scan_ssid -> navigate networks + 'other' for manual typing
        interface.activate()
        print(interface.scan())
        # password -> manual_typing [a-zA-Z0-9!@#$%ˆ&*~-_=+()[]{}<>\|'"`;:/?,.§±]
        # mode: dhcp / manual
        # manual: ip, netmask, gateway, dns
        # check / reset

        config.save()
        
        return config


class Clock:
    def __init__(self):
        self.rtc = machine.RTC()


class Screen:
    def __init__(self, display=None, touch=None):
        if display is None:
            display = _setup_display()
        self.display = display
        self.touch = touch
        self.font = XglcdFont('fonts/Unispace12x24.c', 12, 24)
        
        self.clear()
        
    def clear(self):
        self.display.clear()
        
    def print(self, message, valign="top", halign="left"):
        x, y = 0, 0
        if valign == "center":
            y = (self.display.height - self.font.height) // 2
        
        if halign == "center":
            x = (self.display.width - self.font.measure_text(message)) // 2

        self.display.draw_text(x, y, message, self.font, WHITE)

    def _print_items(self, items, spacing=1):
        height = (self.display.height // (len(items) + 1))  # items + nav options
        text_offset = (height - spacing - self.font.height) // 2

        for i, item in enumerate(items):
            top = i * height
            self.display.fill_hrect(0, top, self.display.width, height - spacing, BLUE)
            self.display.draw_rectangle(0, top, self.display.width, height - spacing, WHITE)
            self.display.draw_text(10, top + text_offset, item[1], self.font, WHITE, BLUE)

    def _print_navbar(self, *nav_options):        
        width = self.display.width // len(nav_options)
        height = self.display.height // 5
        top = self.display.height - height
        text_y_offset = (height - self.font.height) // 2
        
        for i, option in enumerate(nav_options):
            color = WHITE, RED
            if option.startswith("_"):
                color = BLACK, GRAY
                option = option.lstrip("_")
            text_x_offset = (width - self.font.measure_text(option)) // 2
            self.display.fill_hrect(i * width, top, width, height, color[1])
            self.display.draw_rectangle(i * width, top, width, height, WHITE)
            self.display.draw_text(
                i * width + text_x_offset,
                top + text_y_offset,
                option,
                self.font,
                color[0],
                color[1])
            
    def select_item(self, items, extra_button=None):
        self.clear()

        offset = 0
        self._print_items(items[offset:offset + 4])
        self._print_navbar("_<", "manual", ">" if len(items) > 4 else "_>")
        
    def get_network(self, network_interface):
        self.print("scanning networks...", valign="center", halign="center")
        networks = network_interface.scan()
        self.clear()
        items = [(ssid[0], ssid[0].decode("utf-8").strip()) for ssid in networks]
        network = self.select_item(items, extra_button="manual")

class Sensors:
    pass


class Application:
    def __init__(
        self,
        configuration=None,
        clock=None,
        network_interface=None,
        radio=None,
        screen=None,
        sensors=None,
    ):
        print("Initializing app...")
        if configuration is None:
           configuration = Configuration()

        if clock is None:
            clock = Clock()

        if network_interface is None:
            network_interface = NetworkInterface()
            
        if radio is None:
            radio = Radio()

        if screen is None:
            screen = Screen()

        self.configuration = configuration
        self.clock = clock
        self.network_interface = network_interface
        self.radio = radio
        self.screen = screen
        self.sensors = sensors

    def setup(self):
        network_config = self.screen.get_network(self.network_interface)
        
    def run(self):
        print("running...")
        try:
            config = self.configuration.load()
        except MissingConfiguration:
            self.setup()


app = Application()
app.run()
