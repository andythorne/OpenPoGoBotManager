#!/usr/bin/env python

import curses
import json
import os
import shutil
import signal
import subprocess
import sys
from time import sleep

import io
import prettytable
import ruamel.yaml


class ProfileManager():
    def __init__(self):

        with open('config.yml', 'r') as config_file:
            config = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)
            self.bots = config['bots']
            self.bot_directory = config['bot_directory']

        self.bot_processes = {}

        self.screen = curses.initscr()

    def run(self):
        if not self.bot_directory:
            curses.endwin()
            sys.stderr.write(
                "Bot Directory not set\n"
            )
            return

        while True:
            self.screen.clear()
            self.screen.addstr(1, 2, 'OpenPoGoBot Manager')
            self.screen.addstr(2, 2, '===================')
            i = self.draw_profile_table(3, 2)
            self.screen.addstr(i, 4, '1 - Start a bot')
            i += 1
            self.screen.addstr(i, 4, '2 - Stop a bot')
            i += 1
            self.screen.addstr(i, 4, '3 - Show Logs')
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
            elif choice == 'q':
                break

        curses.endwin()

    def draw_profile_table(self, x, y):
        x += 1

        if len(self.bots) == 0:
            return x

        table = prettytable.PrettyTable([
            '#',
            'Bot Name',
            'Config Location',
            'State',
        ])

        # Set table alignment
        table.align['Bot Name'] = 'l'
        table.align['Config Location'] = 'l'
        table.align['State'] = 'l'

        i = 1
        for bot_name in sorted(self.bots.keys()):
            table.add_row([
                i,
                bot_name,
                self.bots[bot_name],
                'Running' if bot_name in self.bot_processes else ''
            ])
            i += 1

        for line in str(table).split('\n'):
            self.screen.addstr(x, y, line)
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

    def start_bot(self):
        self.screen.clear()
        self.screen.addstr(
            1, 2, 'OpenPoGoBot Manager > Start a bot'
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
            bot_name = self.get_bot_name(i, bot_index)
        except ValueError:
            return

        i += 1

        self.screen.addstr(i, 2, 'Selected "{}"!'.format(bot_name))
        i += 1

        if bot_name in self.bot_processes:
            self.screen.addstr(i, 2, 'Bot "{}" is already running!'.format(bot_name))
            self.screen.getch()
            return

        log_file = io.open(bot_name + '.log', 'a')
        p = subprocess.Popen(['python', 'pokecli.py', self.bots[bot_name]], cwd=self.bot_directory,
                             stdout=log_file)

        self.bot_processes[bot_name] = p
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

        if len(self.bots) == 0:
            self.screen.addstr(i, 2, 'Please add an bot first...')
            self.screen.getch()
            return

        self.screen.addstr(i, 2, 'Enter bot number:')
        bot_index = self.screen.getstr(i, 52)

        # Get the profile name from the profile index
        try:
            bot_name = self.get_bot_name(i, bot_index)
        except ValueError:
            return

        i += 1

        if bot_name not in self.bot_processes:
            self.screen.addstr(i, 2, 'Bot "{}" is not running!'.format(bot_name))
            self.screen.getch()
            return

        self.bot_processes[bot_name].terminate()

        del self.bot_processes[bot_name]

        self.screen.addstr(i, 2, 'Bot "{}" has been stopped'.format(bot_name))

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

        if len(self.bots) == 0:
            self.screen.addstr(i, 2, 'Please add an bot first...')
            self.screen.getch()
            return

        self.screen.addstr(i, 2, 'Enter bot number:')
        bot_index = self.screen.getstr(i, 52)

        # Get the profile name from the profile index
        try:
            bot_name = self.get_bot_name(i, bot_index)
        except ValueError:
            return

        i += 1

        if bot_name not in self.bot_processes:
            self.screen.addstr(i, 2, 'Bot "{}" is not running!'.format(bot_name))
            self.screen.getch()
            return

        process = self.bot_processes[bot_name]

        if process.poll() is not None:
            self.screen.addstr(i, 2, 'Bot "{}" has already exited!'.format(bot_name))
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
            with io.open(bot_name + '.log', 'r') as log_file:
                for line in self.tail(log_file, 10):
                    self.screen.addstr(tick_top, 2, line)
                    tick_top += 1

        self.screen.timeout(-1)
        self.screen.getch()

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


if __name__ == '__main__':
    # Create a handler to clean the terminal on SIGINT
    def exit_handler(signal, frame):
        curses.endwin()
        sys.exit(0)


    signal.signal(signal.SIGINT, exit_handler)

    # Create the curses interface
    ProfileManager().run()
