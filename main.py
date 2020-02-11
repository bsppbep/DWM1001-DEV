# coding:utf-8

"""
Author : Quentin GALLOUÉDEC
"""

import os.path
import serial
import time
import re
import logging

from contextlib import suppress

INIT_DELAY = 0.2
CONFIG_DELAY = 2
WRITING_DELAY = 0.01

logging.basicConfig(filename='DWM1001-DEV.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


class DWM1001:
    """Connection with a DWM1001 module through SPI"""

    def __init__(self, port):
        self.port = port
        self.connected = False

    def __enter__(self):
        if not os.path.exists(self.port):
            raise FileNotFoundError(
                'Unable to reach the port {}'.format(self.port))
        self.serial = serial.Serial(
            self.port, timeout=0.5, baudrate=115200, xonxoff=True, exclusive=True)
        logging.info('SPI initialized {}'.format(self.serial))
        time.sleep(CONFIG_DELAY)
        self._begin()
        return self

    def __exit__(self, type, value, traceback):
        self.check_output('quit')
        self.serial.close()
        logging.info('SPI closed')

    def __repr__(self):
        return ('<DWM1001 object mode: {}  network_id: {}'
                '  addr: {}>').format(self.mode, self.network_id, self.addr)

    @property
    def network_id(self):
        return self.__network_id

    @network_id.setter
    def network_id(self, new_network_id):
        self.check_output(' '.join(('nis', new_network_id)))
        self._update_system_info()

    @property
    def abs_position(self):
        return self.__abs_position

    @abs_position.setter
    def abs_position(self, new_abs_position):
        abs_position_str = '{} {} {}'.format(*new_abs_position)
        self.check_output(' '.join(('aps', abs_position_str)))
        self._update_system_info()

    @property
    def anchor_list(self):
        brut_la = ' '.join(self.check_output("la"))
        ids = re.findall('(?<=id=)\S+', brut_la)
        seats = re.findall('(?<=seat=)\S+', brut_la)
        # rssis = re.findall('(?<=rssi=)\S+', brut_la) # Ne fonctionne pas pour les tags
        return [{"id": id, "seat": seat} for id, seat in zip(ids, seats)]

        # return self.__anchor_list

    def _begin(self, max_retries=3):
        """Start the connection with DWM1001"""
        self.connected = False
        self.serial.timeout = 2
        for _ in range(max_retries):
            self.serial.write(b'\r')
            time.sleep(INIT_DELAY)
            self.serial.write(b'\r')
            if 'dwm>' in self._get_response():
                self.connected = True
                self._update_system_info()
                self.serial.timeout = 0.1
                return
        if not(self.connected):
            msg = 'Connection with DWM1001 : '\
                'max retries ({}) exceeded '.format(max_retries)
            logging.error(msg)
            raise RuntimeError(msg)

    def _send_command(self, command):
        """Send a command, and a carraige return"""
        for s in command:
            self.serial.write(s.encode(encoding='ascii'))
            time.sleep(WRITING_DELAY)
        self.serial.write(b'\r')
        logging.debug(' '.join(('written on SPI:', command)))

    def _get_response(self):
        """Read the device answers.
        Set all to True if you don't want to ignore the 'dwm>'
        """
        output = self.serial.readlines()
        decoded_output = [
            encoded_line.decode('ascii').rstrip() for encoded_line in output]
        decoded_output = list(filter(lambda line: line != '', decoded_output))
        logging.debug(' '.join(('read from SPI: ', str(decoded_output))))
        return decoded_output

    def _update_system_info(self):
        """Actualisation of self.mode, self.addr and self.network_id"""
        brut_system_info = ' '.join(self.check_output("si"))
        self.mode = re.search('(?<=mode: )\S+', brut_system_info).group(0)
        self.__network_id = ''.join((
            '0x', re.search('(?<=panid=x)\S+', brut_system_info).group(0)))
        self.addr = ''.join((
            '0x', re.search('(?<=addr=x)\S+', brut_system_info).group(0)))
        brut_abs_position = ' '.join(self.check_output("apg"))
        self.__abs_position = (
            int(re.search('(?<=x:)\S+', brut_abs_position).group(0)),
            int(re.search('(?<=y:)\S+', brut_abs_position).group(0)),
            int(re.search('(?<=z:)\S+', brut_abs_position).group(0)),
        )

    def _update_abs_pos(self):
        brut_abs_position = ' '.join(self.check_output("apg"))
        self.__abs_position = (
            int(re.search('(?<=x:)\S+', brut_abs_position).group(0)),
            int(re.search('(?<=y:)\S+', brut_abs_position).group(0)),
            int(re.search('(?<=z:)\S+', brut_abs_position).group(0)),
        )

    def check_output(self, command=None):
        """Sending a command and return the devide answer"""
        self._send_command(command)
        time.sleep(1)
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
        time.sleep(CONFIG_DELAY)
        self._begin()


def program():
    with DWM1001("/dev/ttyACM0") as device:
        device.set_mode('an')
        device.network_id = "0x1234"
        device.abs_position = (0*320, 4*320, 0)
        print(device)
        print(device.anchor_list)


def plt_live():
    import matplotlib.pyplot as plt
    import numpy
    plt.show()
    ax = plt.gca()
    ax.set_xlim(0, 3200)
    ax.set_ylim(0, 3200)
    line, = ax.plot([0], [0], marker='o', ls='')
    with DWM1001("/dev/ttyACM0") as device:
        # device.set_mode('tn')
        # device.network_id = "0x1234"
        #device.abs_position = (4*320, 4*320, 0)
        # print(device)
        # print(device.anchor_list)
        while True:
            try:
                # device._update_abs_pos()
                # x, y, _ = device.abs_position
                cline = device.serial.readline()
                decoded_line = cline.decode('ascii').rstrip()
                #print(decoded_line)
                try:
                    xyz = re.search('(?<=POS,)\S+,\S+,\S+(?=,)', decoded_line).group(0)
                except:
                    continue
                x, y, z = [float(val) for val in xyz.split(',')]
                print(x, y, z)
                line.set_xdata([0, 0*320, 7*320, 4*320, 1000*x])
                line.set_ydata([0, 4*320, 0*320, 4*320, 1000*y])
                plt.draw()
                plt.pause(1e-17)
                # print(device.check_output("apg"))
            except Exception as err:
                logging.error(err)
                break


def my_second_test():

    with DWM1001("/dev/ttyACM0") as device:
        device.check_output("lec")
        device.serial.timeout = None
        while True:
            try:
                line = device.serial.readline()
                decoded_line = line.decode('ascii').rstrip()
                #print(decoded_line)
                xyz = re.search('(?<=POS,)\S+,\S+,\S+(?=,)', decoded_line).group(0)
                x, y, z = [float(val) for val in xyz.split(',')]
                print(x, y, z)
                
            except Exception as err:
                print(err)
                break


if __name__ == '__main__':
    plt_live()
