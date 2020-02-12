# coding:utf-8

"""
Author : Quentin GALLOUÉDEC
"""

import time
import logging
import serial
import re

INIT_SERIAL_DELAY = 2
WAKE_UP_DELAY = 0.2
WRITING_DELAY = 0.1
MODE_SWITCH_DELAY = 5

logging.basicConfig(filename='DWM1001-DEV.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


class DWM1001:
    """Docstring"""

    def __init__(self, port):
        self.port = port
        self.mode, self.network_id, self.addr = None, None, None

    def __enter__(self):
        self.serial = serial.Serial(self.port, baudrate=115200,
                                    xonxoff=True, exclusive=True)
        logging.info('Serial port opened : {}'.format(str(self.serial)))
        time.sleep(INIT_SERIAL_DELAY)
        self._wake_up()
        return self

    def __exit__(self, type, value, traceback):
        self._quit()
        self.serial.close()
        logging.info('Serial port closed : {}'.format(str(self.serial)))

    def __repr__(self):
        return('<DWM1001 object mode: {}  network_id: {}  addr: '
               '{}>').format(self.mode, self.network_id, self.addr)

    def _wake_up(self, already_failed=False):
        self.send_command('')
        time.sleep(WAKE_UP_DELAY)
        self.send_command('')
        if 'dwm>' not in self.readlines(timeout=1):
            if not already_failed:
                logging.error('Connection to DWM1001 failed once, retrying...')
                self._wake_up(True)
            else:
                logging.critical('Connection to DWM1001 failed')
                raise ConnectionError('Connection to DWM1001 failed')
        else:
            logging.info('Connected to DWM1001')

    def _quit(self):
        self.send_command('quit')
        if 'bye!' in self.readlines():
            logging.info('Disconnected from DWM1001')
        else:
            logging.warning('Failed in disconnecting DWM1001')

    def _brut_anchor_list_to_dict(self, brut_anchor_list):
        brut_anchor_list = brut_anchor_list[2:-2]
        # Each item of brut_anchor_list is something like :
        # '[000576.040 INF]    0) id=000000000000150E seat=0 seens=216 map=0000 pos=0.00:0.00:0.00'
        anchors = []
        for brut_anchor in brut_anchor_list:
            str_pos = re.search('(?<=pos=)\S+', brut_anchor).group(0)
            x_str, y_str, z_str = str_pos = str_pos.split(':')
            anchors.append({
                'id': re.search('(?<=id=)\S+', brut_anchor).group(0),
                'seat': int(re.search('(?<=seat=)\S+', brut_anchor).group(0)),
                'seen': int(re.search('(?<=seens=)\S+', brut_anchor).group(0)),
                'map': re.search('(?<=map=)\S+', brut_anchor).group(0),
                'x': float(x_str),
                'y': float(y_str),
                'z': float(z_str),
            })
        return anchors

    def _brut_meas_pos_to_dict(self, brut_meas_pos):
        # DIST,2,AN0,150E,0.00,0.00,0.00,1.85,AN1,DD34,2.24,0.00,0.00,1.79
        brut_meas_pos_list = brut_meas_pos.split(',')[2:]
        # ['AN0','150E','0.00','0.00','0.00','1.85','AN1','DD34',
        #  '2.24','0.00','0.00','1.79']
        anchors_list, pos = [], None
        i = 0

        # The anchors
        while len(brut_meas_pos_list) > i and brut_meas_pos_list[i][:2] == 'AN':
            brut_anchor = brut_meas_pos_list[i+1:i+6]
            anchors_list.append({
                'id': brut_anchor[0],
                'x': float(brut_anchor[1]),
                'y': float(brut_anchor[2]),
                'z': float(brut_anchor[3])
            })
            i += 6

        if len(brut_meas_pos_list) > i:  # There is pos info
            pos = list(map(float, brut_meas_pos_list[i+1:i+4]))

        return anchors_list, pos

    def send_command(self, command):
        """Send a command"""
        for char in command:
            self.serial.write(char.encode(encoding='ascii'))
            time.sleep(WRITING_DELAY)
        self.serial.write(b'\r')
        logging.debug(' '.join(('written on SPI:', command)))

    def readline(self, timeout=0.1):
        """If a line is available, it returns it. Waits for it otherwise"""
        timeout, self.serial.timeout = self.serial.timeout, timeout
        binary_line = self.serial.readline()  # binary string
        self.serial.timeout = timeout
        line = binary_line.decode('ascii').rstrip()
        logging.debug(' '.join(('read from SPI: ', str(line))))
        return line

    def readlines(self, timeout=0.1):
        """If a list of availables lines"""
        timeout, self.serial.timeout = self.serial.timeout, timeout
        binary_lines = self.serial.readlines()  # List of binary strings
        self.serial.timeout = timeout
        lines = [
            binary_line.decode('ascii').rstrip() for binary_line in binary_lines]
        lines = list(filter(lambda line: line != '', lines))
        logging.debug(' '.join(('read from SPI: ', str(lines))))
        return lines

    def flush(self):
        self.readlines(0.1)

    def set_mode(self, mode):
        """Choose between 'tag', 'tag_listener', 'anchor' or 'anchor_initiator' """
        mode_command = {
            'anchor_initiator': 'nmi',
            'anchor': 'nma',
            'tag': 'nmt',
            #'tag_listener': 'nmtl'
            'listener': 'nmp'
        }
        command = mode_command[mode]
        self.send_command(command)
        self.flush()
        logging.info('Turn mode into {}. Reconnection needed.'.format(mode))
        time.sleep(MODE_SWITCH_DELAY)
        self._wake_up()

    def get_mode(self):
        self.send_command('nmg')
        return self.readlines()

    def set_network_id(self, network_id):
        """Choose hex id from '0x0000 to '0XFFFF' """
        self.send_command(' '.join(('nis', network_id)))

    def set_position(self, x, y, z):
        """For anchor only. Set the position in meters"""
        xyz_mm_str = str(int(1000*x)), str(int(1000*y)), str(int(1000*z))
        self.send_command(' '.join(('aps', *xyz_mm_str)))

    def get_anchor_list(self):
        """For tag only. Returns a list of dict('id', 'pos')"""
        self.flush()
        self.send_command('la')
        brut_anchor_list = self.readlines()
        if brut_anchor_list[0] != 'la' or brut_anchor_list[-1] != 'dwm>':
            logging.warning('Unable to read the output')
            raise RuntimeError('Unable to read the output')
        return self._brut_anchor_list_to_dict(brut_anchor_list)

    def get_system_information(self):
        self.send_command('si')
        return self.readlines()

    def is_listen_mode(self):
        time.sleep(1)
        self.flush()
        return bool(device.readline(11))

    def set_listen_mode(self, decision):
        if decision != self.is_listen_mode():
            self.send_command('lec')
            self.flush()


def print_meas_pos(device):
    #device.set_listen_mode(True)
    while True:
        try:
            print(device.readline(None))
        except KeyboardInterrupt:
            break

def plt_live(device):
    import matplotlib.pyplot as plt
    import numpy
    plt.show()
    ax = plt.gca()
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    line, = ax.plot([0], [0], marker='o', ls='')

    while True:
        try:
            output = device.readline(None).split(',')
            print("output", output)
            x, y, z = list(map(float, output[3:6]))
            print("x y z ", x, y, z)
            print(device.get_anchor_list())
            line.set_xdata([0, 0, 7, 4, x/0.32])
            line.set_ydata([0, 4, 0, 4, y/0.32])
            plt.draw()
            plt.pause(1e-17)
        except Exception as error:
            print(error)
            time.sleep(0.1)
            continue


if __name__ == '__main__':
    with DWM1001('/dev/ttyACM0') as device:
        #device.set_mode('listener')
        #device.set_network_id('0x1234')
        #device.set_position(0*0.320, 4*0.320, 0)
        #device.set_listen_mode(True)
        # while True:
        #     print(device.get_anchor_list())
        plt_live(device)
        # device.send_command('si')
        # device.readlines()
        
