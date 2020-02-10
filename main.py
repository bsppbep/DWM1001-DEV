# coding:utf-8

"""
Author : Quentin GALLOUÉDEC
"""

import serial
import time
import re

INIT_DELAY = 0.5


class DWM1001:
    """Connection with a DWM1001 module through SPI"""

    def __init__(self, port):
        self.port = port
        self.connected = False

    def __enter__(self):
        self.serial = serial.Serial(self.port, timeout=0.1, baudrate=115200)
        time.sleep(INIT_DELAY)
        self._begin()
        return self

    def __exit__(self, type, value, traceback):
        self.serial.close()

    def __repr__(self):
        return ('<DWM1001 object mode: {}  network_id: {}'
                '  addr: {}>').format(self.mode, self.network_id, self.addr)

    def _begin(self, max_retries=3):
        """Start the connection with DWM1001"""
        for _ in range(max_retries):
            self._send_command()
            time.sleep(INIT_DELAY)
            if 'dwm>' in self._get_response(all=True):
                self.connected = True
                self._update_system_info()
                return
        if not(self.connected):
            raise RuntimeError(
                "Connection with DWM1001 : max retries exceeded")

    def _send_command(self, command=None):
        """Send a command, and a carraige return"""
        if command is not None:
            self.serial.write(command.encode(encoding='ascii'))
        self.serial.write(b'\r')

    def _get_response(self, all=False):
        """Read the device answers.
        Set all to True if you don't want to ignore the 'dwm>'
        """
        start_idx = 0 if all else 1
        output = self.serial.readlines()[start_idx:]
        decoded_output = [
            encoded_line.decode('ascii').rstrip() for encoded_line in output]
        return list(filter(lambda line: line != '', decoded_output))

    def _update_system_info(self):
        """Actualisation of self.mode, self.addr and self.network_id"""
        brut_system_info = ' '.join(self.check_ouput("si"))
        self.mode = re.search('(?<=mode: )\S+', brut_system_info).group(0)
        self.network_id = ''.join((
            '0x', re.search('(?<=panid=x)\S+', brut_system_info).group(0)))
        self.addr = ''.join((
            '0x', re.search('(?<=addr=x)\S+', brut_system_info).group(0)))

    def _re_open(self):
        self.__exit__(None, None, None)
        self.__enter__()

    def check_ouput(self, command=None):
        """Sending a command and return the devide answer"""
        self._send_command(command)
        return self._get_response()

    def set_mode(self, mode):
        """Set a new mode
        Args:
            mode (str): 'ani', 'an' or 'tn'
        """
        if mode == 'ani':
            command = 'nmi'
        elif mode == 'an':
            command = 'nma'
        elif mode == 'tn':
            command = 'nmt'

        self._send_command(command)
        self._re_open()


if __name__ == '__main__':
    with DWM1001("/dev/ttyACM0") as device:
        device.set_mode('ani')
        print(device)
        device.set_mode('an')
        print(device)
        device.set_mode('tn')
        print(device.check_ouput('la'))
