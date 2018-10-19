#!/usr/bin/env python3
import urwid
import logging
from Sinamics_Canopen.sinamics import SINAMICS
from can import CanError

# import pydevd
# pydevd.settrace('localhost', port=8000, stdoutToServer=True, stderrToServer=True)


# instantiate object
inverter = SINAMICS()


class urwidHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a urwid section.
    """
    _urwid_log = []

    def __init__(self):
        logging.Handler.__init__(self)
        formatter = logging.Formatter('%(name)-20s: %(levelname)-8s %(message)s')
        self.setLevel(logging.INFO)
        self.setFormatter(formatter)
        self._urwid_log = [urwid.Text(''), urwid.Text(''), urwid.Text('')]

    def emit(self, record):
        """
        Update message to urwid logger field.
        """
        msg = self.format(record)
        # swap to bottom
        self._urwid_log[2].set_text(self._urwid_log[1]._text)
        self._urwid_log[1].set_text(self._urwid_log[0]._text)
        # add new
        self._urwid_log[0].set_text(msg)

    def get_log(self):
        return self._urwid_log


class Interface:
    """
    TODO
    """
    # menu options
    main_choices = None
    # main menu handler
    main_menu = None
    menu_render = None
    # frame components for speed report
    body_speed = None
    header_speed = None

    # frame components for current report
    body_current = None
    header_current = None
    # frame components for logger report
    header_logger = None
    # vertical stack pile
    rows = []
    body_logger = None
    pile = None
    rows_filler = None
    v_padding = None
    rows_box = None
    state = False

    def __init__(self, title=None, menu_choices=None):
        self.main_choices = menu_choices
        self.menu(title, menu_choices)

        # create frame for speed report
        self.body_speed = urwid.Text('{0:+05d} RPM'.format(0))
        self.header_speed = urwid.Text(['Estimated Speed'])

        # create frame for current report
        self.body_current = urwid.Text('{0:+08.2f} Arms'.format(0))
        self.header_current = urwid.Text(['Estimated Current smoothed'])

        # create frame for logger
        self.header_logger = urwid.Text('Last 3 log messages')
        # create menu frame
        self.main_menu = urwid.Padding(self.menu_render, align='center', left=1, width=20)

        # set up logging to file - see previous section for more details
        logging.basicConfig(level=logging.DEBUG,
                            format='[%(asctime)s.%(msecs)03d] [%(name)-20s]: %(levelname)-8s %(message)s',
                            datefmt='%d-%m-%Y %H:%M:%S',
                            filename='my_log.log',
                            filemode='w')
        # create handler for logger
        root_logger = logging.getLogger('')
        self.body_logger = urwidHandler()
        root_logger.addHandler(self.body_logger)
        # add speed
        self.rows.append(self.header_speed)
        self.rows.append(self.body_speed)
        self.rows.append(urwid.Divider('-', top=0, bottom=0))
        # add current
        self.rows.append(self.header_current)
        self.rows.append(self.body_current)
        self.rows.append(urwid.Divider('-', top=0, bottom=0))
        # add logger
        self.rows.append(self.header_logger)
        self.rows.extend(self.body_logger._urwid_log)
        self.rows.append(urwid.Divider('-', top=0, bottom=0))
        # add menu
        self.rows.append((6, self.main_menu))
        # add all vertically
        self.pile = urwid.Pile(self.rows)
        # surround by a filler
        self.rows_filler = urwid.Filler(self.pile, valign='top', top=1, bottom=1)
        # add padding to left and right
        self.v_padding = urwid.Padding(self.rows_filler, left=1, right=1)
        # surround by a box
        self.rows_box = urwid.LineBox(self.v_padding)

    def menu(self, title, choices):
        """
        TODO
        :param title:
        :param choices:
        :return:
        """
        body = [urwid.Text(title), urwid.Divider()]
        for c in choices:
            button = urwid.Button(c)
            urwid.connect_signal(button, 'click', self.item_chosen, c)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        # append quit option
        quit_button = urwid.Button('Quit')
        urwid.connect_signal(quit_button, 'click', self.exit_program)
        body.append(urwid.AttrMap(quit_button, None, focus_map='reversed'))
        self.menu_render = urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def return_main(self, button):
        self.main_menu.original_widget = urwid.Padding(self.menu_render)

    def set_seed(self, button, response):
        self.body_speed.set_text('{0:+05d} RPM'.format(response.value()))
        self.main_menu.original_widget = urwid.Padding(self.menu_render)

    def item_chosen(self, button, choice):
        if choice == 'Toggle ON/OFF':
            # if is enable, disable it
            if self.state:
                # inverter.writeObject(0x6040, 0, (0).to_bytes(2, 'little'))
                inverter.changeState('shutdown')
                self.state = False
            else:
                inverter.writeObject(0x6040, 0, (15).to_bytes(2, 'little'))
                # inverter.changeState('enable operation')
                self.state = True
            response = urwid.Text(['Inverter is {0}'.format(('ON' if self.state else 'OFF')), u'\n'])
            done = urwid.Button(u'Ok')
            urwid.connect_signal(done, 'click', self.return_main)
            self.main_menu.original_widget = urwid.Filler(
                urwid.Pile([response, urwid.AttrMap(done, None, focus_map='reversed')]))
        elif choice == 'Set Speed':
            response = urwid.IntEdit('Enter RPMs\n', default=0)
            done = urwid.Button(u'Ok')
            urwid.connect_signal(done, 'click', self.set_seed, response)
            self.main_menu.original_widget = urwid.Filler(
                urwid.Pile([response, urwid.AttrMap(done, None, focus_map='reversed')]))

    def exit_program(self, button):
        raise urwid.ExitMainLoop()

    def quit_on_q(self, key):
        if key == 'q':
            raise urwid.ExitMainLoop

    def trigger_log(self, loop=None, data=None):
        if not data:
            return
        logging.info(data)

def main():
    """Test SINAMICS CANopen communication with some examples.

        Use a few examples to test communication with SINAMICS device using
        a few functions. Also resets the fault error if present.

        Show sample using also the EDS file.
    """

    def print_message(message):
        logging.debug('{0} received'.format(message.name))
        # print("--")
        for var in message:
            logging.debug('{0} = {1:06X}'.format(var.name, var.raw))

        # inverter.printCurrentSmoothed()
        # inverter.printTorqueSmoothed()

    import argparse
    import sys
    from time import sleep

    if sys.version_info < (3, 0):
        print("Please use python version 3")
        return

    parser = argparse.ArgumentParser(add_help=True,
                                     description='Test SINAMICS CANopen Communication')
    parser.add_argument('--channel', '-c', action='store', default='can0',
                        type=str, help='Channel to be used', dest='channel')
    parser.add_argument('--bus', '-b', action='store',
                        default='socketcan', type=str, help='Bus type', dest='bus')
    parser.add_argument('--rate', '-r', action='store', default=None,
                        type=int, help='bitrate, if applicable', dest='bitrate')
    parser.add_argument('--nodeID', action='store', default=2, type=int,
                        help='Node ID [ must be between 1- 127]', dest='nodeID')
    parser.add_argument('--objDict', action='store', default='sinamics_s120.eds',
                        type=str, help='Object dictionary file', dest='objDict')
    args = parser.parse_args()

    # construct interface
    main_choices = ['Toggle ON/OFF', 'Set Speed', 'Change V/F']
    interface = Interface(title='Sinamics Options', menu_choices=main_choices)

    main_loop = urwid.MainLoop(interface.rows_box, unhandled_input=interface.quit_on_q)

    if not (inverter.begin(args.nodeID, objectDictionary=args.objDict)):
        logging.info('Failed to begin connection with SINAMICS device')
        logging.info('Exiting now')
        return -1

    try:
        # testing pdo objects
        inverter.node.pdo.read()
        # Save new configuration (node must be in pre-operational)
        inverter.node.nmt.state = 'PRE-OPERATIONAL'
        # inverter.node.pdo.save()'

        inverter.node.pdo.tx[1].clear()
        inverter.node.pdo.tx[2].clear()
        inverter.node.pdo.tx[3].clear()
        inverter.node.pdo.tx[4].clear()

        inverter.node.pdo.rx[1].clear()
        inverter.node.pdo.rx[2].clear()
        inverter.node.pdo.rx[3].clear()
        inverter.node.pdo.rx[4].clear()

        inverter.node.pdo.tx[2].add_variable(0x6041, 0, 16)
        inverter.node.pdo.tx[2].add_variable(0x606C, 0, 32)
        inverter.node.pdo.tx[2].enabled = True
        # inverter.node.pdo.tx[2].event_timer = 2000
        inverter.node.pdo.tx[2].trans_type = 254
        # reset
        inverter.changeState('fault reset')
        sleep(0.1)
        # Save parameters to device and change to pre-operational
        inverter.node.nmt.state = 'PRE-OPERATIONAL'
        inverter.node.pdo.tx[2].save()

        # Add callback for message reception
        inverter.node.pdo.tx[2].add_callback(print_message)

        # Set back into operational mode
        inverter.node.nmt.state = 'OPERATIONAL'
        sleep(0.1)
        inverter.writeObject(0x6040, 0, (6).to_bytes(2, 'little'))
        # inverter.changeState('shutdown')
        sleep(0.1)
        inverter.writeObject(0x6040, 0, (7).to_bytes(2, 'little'))
        # inverter.changeState('switch on')
        sleep(0.1)
        # inverter.writeObject(0x6040, 0, (15).to_bytes(2, 'little'))
        # inverter.changeState('enable operation')
        main_loop.run()
    except KeyboardInterrupt as e:
        logging.info('Got {0}... exiting now'.format(e))
        raise urwid.ExitMainLoop
    except CanError:
        print("Message NOT sent")
        raise urwid.ExitMainLoop
    except:
        raise urwid.ExitMainLoop
    finally:
        # inverter.network.sync.stop()
        inverter.node.nmt.state = 'PRE-OPERATIONAL'
        inverter.setTargetVelocity(0)
        # inverter.writeObject(0x6040, 0, (0).to_bytes(2, 'little'))
        inverter.changeState('shutdown')
    return


if __name__ == '__main__':
    main()
