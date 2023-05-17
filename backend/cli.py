#!/usr/bin/env python3
import os
import re
import sys

import curses

from plexwrapper import PlexWrapper


class CleanarrCli:
    def __init__(self):
        self.wrapper = PlexWrapper()
        self.items_obj = {}

    @staticmethod
    def validate_env():
        valid = True
        envs = ("PLEX_BASE_URL", "PLEX_TOKEN", "LIBRARY_NAMES")
        for env in envs:
            if env not in os.environ:
                valid = False
                print("Environment variable {} not found".format(env))
        if valid is False:
            raise Exception("Please provide all environment variables {}".format(envs))

    # Curses section
    @staticmethod
    def draw_checkbox(win, y, x, checked):
        try:
            if checked:
                win.addstr(y, x, "[X] ")
            else:
                win.addstr(y, x, "[ ] ")
        except Exception as err:
            print(err)
            pass

    @staticmethod
    def format_bytes(fbytes):
        if fbytes >= 1024**3:  # GB
            return f"{fbytes / (1024**3):.2f} GB"
        elif fbytes >= 1024**2:  # MB
            return f"{fbytes / (1024**2):.2f} MB"
        elif fbytes >= 1024:  # KB
            return f"{fbytes / 1024:.2f} KB"
        else:
            return f"{fbytes} bytes"

    def start_curses(self, stdscr):
        curses.curs_set(0)

        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

        # Initialize the list of items and checkboxes
        items = []
        self.items_obj = {}
        firsts = []
        dupes = self.get_all_dupes()
        for dupe in dupes:
            is_first = True
            for media in dupe["media"]:
                for part in media["parts"]:
                    if is_first is True:
                        firsts.append(len(items))
                        is_first = False
                    items.append(
                        f"{dupe['title']} - {part['file']} @ {self.format_bytes(part['size'])} [{media['id']}]"
                    )
                    self.items_obj[media["id"]] = {
                        "dupe": dupe,
                    }

        checkboxes = [True] * len(items)
        for first in firsts:
            checkboxes[first] = False
        current_index = 0
        top_row = 0
        bottom_row = min(curses.LINES - 2, len(items))
        continue_with_delete = False

        while True:
            stdscr.clear()

            for i in range(top_row, bottom_row):
                if i == current_index:
                    stdscr.attron(curses.color_pair(2))
                    self.draw_checkbox(stdscr, i - top_row, 0, checkboxes[i])
                    stdscr.addstr(i - top_row, 4, items[i])
                    stdscr.attroff(curses.color_pair(2))
                else:
                    self.draw_checkbox(stdscr, i - top_row, 0, checkboxes[i])
                    stdscr.addstr(i - top_row, 4, items[i])

            stdscr.refresh()

            key = stdscr.getch()

            # Process user input
            if key == curses.KEY_UP and current_index > 0:
                current_index -= 1
                if current_index < top_row:
                    top_row -= 1
                    bottom_row -= 1
            elif key == curses.KEY_DOWN and current_index < len(items) - 1:
                current_index += 1
                if current_index >= bottom_row:
                    top_row += 1
                    bottom_row += 1
            elif key == ord(" "):
                checkboxes[current_index] = not checkboxes[current_index]
            elif key == ord("\n"):
                confirm_win = curses.newwin(5, curses.COLS - 2, curses.LINES - 7, 1)
                confirm_win.box()
                confirm_win.addstr(1, 2, "Are you sure you want to delete these?")
                confirm_win.addstr(4, 2, "[Y] Yes    [N] No")
                confirm_win.refresh()

                while True:
                    confirm_key = confirm_win.getch()
                    if confirm_key == ord("y") or confirm_key == ord("Y"):
                        confirm_win.clear()
                        confirm_win.refresh()
                        confirm_win.addstr(1, 2, "I shall continue with deletion!")
                        confirm_win.refresh()
                        continue_with_delete = True
                        # Continue with the program and handle deletion logic
                        break
                    elif confirm_key == ord("n") or confirm_key == ord("N"):
                        confirm_win.clear()
                        confirm_win.refresh()
                        confirm_win.addstr(1, 2, "Deletion canceled!")
                        confirm_win.refresh()
                        # Continue with the program
                        break

                if continue_with_delete is True:
                    break

        if continue_with_delete is True:
            for i, checkbox in enumerate(checkboxes):
                if checkbox is True:
                    match = re.search(r"\[(\d+)\]", items[i])
                    if not match:
                        print(
                            "Silently erroring: could not find media ID in {}".format(
                                items[i]
                            )
                        )
                        continue
                    self.delete_media(int(match.group(1)))

    def delete_media(self, media_id):
        content_key = self.items_obj[media_id]["dupe"]["key"]
        library_name = self.items_obj[media_id]["dupe"]["library"]
        print(f"Deleting {media_id} {content_key} in {library_name}".format(media_id))
        return self.wrapper.delete_media(
            library_name=library_name, content_key=content_key, media_id=media_id
        )

    # PlexWrapper section
    def get_dupe_content(self, page=1):
        print("Getting duplicate content for page {}".format(page))
        return self.wrapper.get_dupe_content(page)

    def get_all_dupes(self):
        page = 1
        dupes = []
        while True:
            content = self.get_dupe_content(page)
            if len(content) == 0:
                break
            dupes.extend(content)
            page += 1
        return dupes

    def dupe_content_summary(self):
        dupes = self.get_all_dupes()
        for dupe in dupes:
            print(dupe["title"])
            for media in dupe["media"]:
                for part in media["parts"]:
                    print("  {}".format(part["file"]))
        return dupes


if __name__ == "__main__":
    # environment validation
    try:
        CleanarrCli.validate_env()
    except Exception as err:
        print(err)
        sys.exit(1)

    cli = CleanarrCli()
    curses.wrapper(cli.start_curses)
