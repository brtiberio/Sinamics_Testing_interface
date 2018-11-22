#!/usr/bin/env python3
import urwid
import logging

# import pydevd
# pydevd.settrace('localhost', port=8000, stdoutToServer=True, stderrToServer=True)


class urwidHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a urwid section.
    """
    _urwid_log = []

    def __init__(self):
        logging.Handler.__init__(self)
        self._urwid_log = urwid.Text('')

    def emit(self, record):
        """
        Update message to urwid logger field.
        """
        msg = self.format(record)
        self._urwid_log.set_text(msg)

    def get_log(self):
        return self._urwid_log


main_choices = ['Toggle ON/OFF', 'Set Speed', 'Change V/F']


def menu(title, choices):
    body = [urwid.Text(title), urwid.Divider()]
    for c in choices:
        button = urwid.Button(c)
        urwid.connect_signal(button, 'click', item_chosen, c)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    # append quit option
    quit_button = urwid.Button('Quit')
    urwid.connect_signal(quit_button, 'click', exit_program)
    body.append(urwid.AttrMap(quit_button, None, focus_map='reversed'))
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def return_main(button):
    main_menu.original_widget = urwid.Padding(menu_render)


def set_seed(button, response):
    try:
        velocity = int(response.edit_text)
        body_speed.set_text('{0:+05d} RPM'.format(velocity))
    except ValueError:
        logging.info("Velocity value must be an integer")
    finally:
        main_menu.original_widget = urwid.Padding(menu_render)



def item_chosen(button, choice):
    if choice == 'Toggle ON/OFF':
        response = urwid.Text([u'You chose ', choice, u'\n'])
        done = urwid.Button(u'Ok')
        urwid.connect_signal(done, 'click', return_main)
        main_menu.original_widget = urwid.Filler(
            urwid.Pile([response, urwid.AttrMap(done, None, focus_map='reversed')]))
    elif choice == 'Set Speed':
        response = urwid.Edit(caption='Enter RPMs\n', edit_text='0')
        done = urwid.Button(u'Ok')
        urwid.connect_signal(done, 'click', set_seed, response)
        main_menu.original_widget = urwid.Filler(
            urwid.Pile([response, urwid.AttrMap(done, None, focus_map='reversed')]))


def exit_program(button):
    raise urwid.ExitMainLoop()


def quit_on_q(key):
    if key == 'q':
        raise urwid.ExitMainLoop


def trigger_log(loop=None, data=None):
    logging.info("here is some text without meaning!")
    return


# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] [%(name)-12s] [%(levelname)-8s] %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='mylog.log',
                    filemode='w')
# create handler for logger
formatter = logging.Formatter('%(name)-20s: %(levelname)-8s %(message)s')
root_logger = logging.getLogger('')
body_logger = urwidHandler()
body_logger.setLevel(logging.INFO)
body_logger.setFormatter(formatter)
root_logger.addHandler(body_logger)


# create frame for speed report
body_speed = urwid.Text('{0:+05d} RPM'.format(0))
header_speed = urwid.Text(['Estimated Speed'])

# create frame for current report
body_current = urwid.Text('{0:+08.2f} Arms'.format(0))
header_current = urwid.Text(['Estimated Current smoothed'])
# create logger window
header_logger = urwid.Text('Last 3 log messages')


menu_render = menu(u'Sinamics options', main_choices)
main_menu = urwid.Padding(menu_render, align='center', left=1, width=20)

rows = []
rows.append(header_speed)
rows.append(body_speed)
rows.append(urwid.Divider('-', top=1, bottom=1))
rows.append(header_current)
rows.append(body_current)
rows.append(urwid.Divider('-', top=2, bottom=2))
rows.append(header_logger)
rows.append(body_logger._urwid_log)
rows.append(urwid.Divider('-', top=2, bottom=2))
rows.append((6, main_menu))

pile = urwid.Pile(rows)
rows_filler = urwid.Filler(pile, valign='top', top=1, bottom=1)
v_padding = urwid.Padding(rows_filler, left=1, right=1)
rows_box = urwid.LineBox(v_padding)

main_loop = urwid.MainLoop(rows_box,  unhandled_input=quit_on_q)
main_loop.set_alarm_in(5, trigger_log)
main_loop.run()
