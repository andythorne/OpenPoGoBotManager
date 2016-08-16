#!/usr/bin/env python
# coding=UTF-8

import curses
import json
import os
import signal
import subprocess
import sys
import locale

from tabulate import tabulate
import io
import ruamel.yaml

locale.setlocale(locale.LC_ALL, '')

class ProfileManager():
    def __init__(self):

        with open('config.yml', 'r') as config_file:
            config = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)
            self.bots = config['bots']
            self.bot_directory = config['bot_directory']

        self.current_bot = None
        self.bot_states = {}
        self.bot_processes = {}

        self._read_bot_states()
        self._write_bot_states()

        self.screen = curses.initscr()
        curses.start_color()

    def run(self):
        if not self.bot_directory:
            curses.endwin()
            sys.stderr.write(
                'Bot Directory not set\n'
            )
            return

        while not self.current_bot:
            self.select_bot()

        while True:
            self.screen.clear()
            self.screen.addstr(1, 2, 'OpenPoGoBot Manager')
            self.screen.addstr(2, 2, '===================')
            i = self.draw_profile_table(3, 2)
            self.screen.addstr(i, 4, '1 - Start bot')
            i += 1
            self.screen.addstr(i, 4, '2 - Stop bot')
            i += 1
            self.screen.addstr(i, 4, '3 - Show Logs')
            i += 1
            self.screen.addstr(i, 4, 'c - Change Bot')
            i += 1
            self.screen.addstr(i, 4, 'q - Exit')
            i += 2
            self.screen.addstr(i, 4, 'Choose an option: ')
            choice = self.screen.getstr(i, 22)

            if choice == '1':
                self.start_bot()
            elif choice == '2':
                self.stop_bot()
            elif choice == '3':
                self.bot_log()
            elif choice == 'c':
                self.current_bot = None
                while not self.current_bot:
                    self.select_bot()
            elif choice == 'q':
                break

        curses.endwin()

    def draw_profile_table(self, x, y):
        x += 1

        if len(self.bots) == 0:
            return x

        table_headers = [
            '#',
            'Bot Name',
            'Config Location',
            'State',
        ]
        table_rows = []

        i = 1
        for bot_name in sorted(self.bots.keys()):
            is_current_bot = False
            if bot_name == self.current_bot:
                is_current_bot = True
            table_rows.append([
                str(i) + ('*' if is_current_bot else ''),
                bot_name,
                self.bots[bot_name],
                u'\u2713' if self.is_bot_running(bot_name) else ''
            ])
            i += 1

        table = tabulate(table_rows, headers=table_headers, tablefmt='psql')
        for line in table.split('\n'):
            self.screen.addstr(x, y, line.encode('utf-8'))
            x += 1

        return x + 1

    def get_bot_name(self, i, bot_index):
        # Validate the given profile index
        try:
            int(bot_index)
        except ValueError:
            i += 2
            self.screen.addstr(i, 2, 'Not a valid profile number...')
            self.screen.getch()
            raise

        if int(bot_index) <= 0:
            i += 2
            self.screen.addstr(i, 2, 'Not a valid bot number...')
            self.screen.getch()
            raise ValueError

        try:
            bot_name = sorted(self.bots.keys())[int(bot_index) - 1]
        except IndexError:
            i += 2
            self.screen.addstr(i, 2, 'No Bot found with that number...')
            self.screen.getch()
            raise ValueError

        return bot_name

    def select_bot(self):
        self.screen.clear()
        self.screen.addstr(
            1, 2, 'OpenPoGoBot Manager > Select bot'
        )
        self.screen.addstr(
            2, 2, '================================='
        )
        i = self.draw_profile_table(3, 2)

        if len(self.bots) == 0:
            self.screen.addstr(i, 2, 'Please add an bot first...')
            self.screen.getch()
            return

        self.screen.addstr(i, 2, 'Enter bot number:')
        bot_index = self.screen.getstr(i, 52)

        # Get the profile name from the profile index
        try:
            self.current_bot = self.get_bot_name(i, bot_index)
        except ValueError:
            return

    def start_bot(self):
        self.screen.clear()
        self.screen.addstr(
            1, 2, 'OpenPoGoBot Manager > Start a bot'
        )
        self.screen.addstr(
            2, 2, '================================='
        )
        i = self.draw_profile_table(3, 2)
        i += 1

        if self.current_bot in self.bot_states:
            self.screen.addstr(i, 2, 'Bot "{}" is already running!'.format(self.current_bot))
            self.screen.getch()
            return

        log_file = io.open(self.current_bot + '.log', 'a')
        p = subprocess.Popen(['python', 'pokecli.py', self.bots[self.current_bot]], cwd=self.bot_directory,
                             stdout=log_file, stderr=log_file)

        self.bot_states[self.current_bot] = {
            'pid': p.pid,
        }
        self._write_bot_states()

        self.bot_processes[self.current_bot] = p

        self.screen.addstr(i, 2, 'Started "{}"!'.format(self.current_bot))
        i += 1

        self.screen.getch()

    def stop_bot(self):
        self.screen.clear()
        self.screen.addstr(
            1, 2, 'OpenPoGoBot Manager > Stop a bot'
        )
        self.screen.addstr(
            2, 2, '================================='
        )
        i = self.draw_profile_table(3, 2)
        i += 1

        if self.current_bot not in self.bot_states:
            self.screen.addstr(i, 2, 'Bot "{}" is not running!'.format(self.current_bot))
            self.screen.getch()
            return

        try:
            self.bot_processes[self.current_bot].terminate()
            del self.bot_processes[self.current_bot]
        except OSError:
            pass  # process already dead

        del self.bot_states[self.current_bot]
        self._write_bot_states()

        self.screen.addstr(i, 2, 'Bot "{}" has been stopped'.format(self.current_bot))

        self.screen.getch()

    def bot_log(self):
        self.screen.clear()
        self.screen.addstr(
            1, 2, 'OpenPoGoBot Manager > Bot Log'
        )
        self.screen.addstr(
            2, 2, '================================='
        )
        i = self.draw_profile_table(3, 2)
        i += 1

        if self.current_bot not in self.bot_states:
            self.screen.addstr(i, 2, 'Bot "{}" is not running!'.format(self.current_bot))
            self.screen.getch()
            return

        i += 1

        self.screen.timeout(1)
        log_top = i
        while True:
            pressed = self.screen.getch()
            if pressed == ord('q'):
                break

            tick_top = log_top
            with io.open(self.current_bot + '.log', 'r') as log_file:
                for line in self.tail(log_file, 10):
                    self.screen.addstr(tick_top, 2, line)
                    tick_top += 1

        self.screen.timeout(-1)
        self.screen.getch()

    def is_bot_running(self, bot_name):
        if bot_name in self.bot_processes:
            if self.bot_processes[bot_name].poll() is None:
                return True

        if bot_name in self.bot_states:
            pid = self.bot_states[bot_name]['pid']
            if os.path.exists('/proc/' + str(pid)):
                return True

        return False

    @staticmethod
    def tail(f, n):
        assert n >= 0
        pos, lines = n + 1, []
        while len(lines) <= n:
            try:
                f.seek(-pos, 2)
            except IOError:
                f.seek(0)
                break
            finally:
                lines = list(f)
            pos *= 2
        return lines[-n:]

    def _write_bot_states(self):
        with open('.manager.json', 'w+') as bot_states_cache:
            bot_states_cache.write(json.dumps(self.bot_states))

    def _read_bot_states(self):
        if os.path.isfile('.manager.json'):
            with open('.manager.json', 'r') as dot_manager:
                self.bot_states = json.load(dot_manager)

        for bot_name in self.bot_states.copy():
            bot_state = self.bot_states[bot_name]
            if not os.path.exists('/proc/' + str(bot_state['pid'])):
                del self.bot_states[bot_name]

if __name__ == '__main__':
    # Create a handler to clean the terminal on SIGINT
    def exit_handler(signal, frame):
        curses.endwin()
        sys.exit(0)


    signal.signal(signal.SIGINT, exit_handler)

    # Create the curses interface
    ProfileManager().run()
