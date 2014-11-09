#!/usr/bin/env python

import argparse
import sys
import os
from Tkinter import Button, Label, Tk, Frame, TOP, mainloop
from PIL import Image, ImageTk

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import dfr.db
from dfr.bit_equal_finder import BitEqualFinder
from dfr.bit_truncated_finder import BitTruncatedFinder
from dfr.image_similar_finder import ImageSimilarFinder
from dfr.support import format_bytes, add_common_command_line_arguments


class InteractiveResolver(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run

    def _delete(self, to_delete):
        assert len(to_delete) >= 1
        for path in to_delete:
            if self.dry_run:
                print "(dry-run) Would remove %s" % path
            else:
                os.remove(path)


class CsvBitEqualResolver(object):
    def __init__(self):
        print "size;hardlinked;path1;path2"

    # pylint: disable=R0201
    def resolve(self, pair):
        print "%d;%s;%s;%s" % (
            pair.size, pair.hardlinked, pair.path1, pair.path2)

    def finished(self):
        pass


class InteractiveBitEqualResolver(InteractiveResolver):
    def __init__(self, dry_run):
        InteractiveResolver.__init__(self, dry_run)
        self.default_preserve = None

    def _evaluate_input(self, input, pair):
        if input == "a":
            if pair.hardlinked:
                print "Error: Will not remove both hardlinked files."
                return None
            else:
                to_delete = [pair.path1, pair.path2]
        elif input == "s":
            return []
        elif input == "1!":
            to_delete = [pair.path2]
            self.default_preserve = 1
        elif input == "2!":
            to_delete = [pair.path1]
            self.default_preserve = 2
        else:
            try:
                choice = int(input)
            except ValueError:
                return None
            if choice not in [1, 2]:
                return None
            if choice == 1:
                to_delete = [pair.path2]
            elif choice == 2:
                to_delete = [pair.path1]
            else:
                assert 0
        return to_delete

    # pylint: disable=R0913
    def resolve(self, pair):
        progress = "[%d.%d/%d] " % (
            pair.ctxt_index+1, pair.ctxt_subindex+1, pair.ctxt_size)

        print "\nThe following files are equal and %s bytes large" % (
            format_bytes(pair.size))
        while True:
            print "  [1] %s" % pair.path1
            print "  [2] %s" % pair.path2
            msg = progress+"sPreserve what? Press 1, 2, "
            if not pair.hardlinked:
                msg += "'a' (to delete all), "
            msg += "'s' (to skip)."
            print msg

            if self.default_preserve:
                if self.default_preserve == 1:
                    to_delete = [pair.path2]
                elif self.default_preserve == 2:
                    to_delete = [pair.path1]
                else:
                    assert 0
            else:
                input = raw_input("> ")
                to_delete = self._evaluate_input(input, pair)
                if to_delete is None:
                    continue
                elif to_delete == []:
                    break

            self._delete(to_delete)
            break

    def finished(self):
        pass


class CsvBitTruncatedResolver(object):
    def __init__(self):
        print "largesize;largepath;smallsize;smallpath"

    # pylint: disable=R0201
    def resolve(self, pair):
        print "%d;%s;%s;%s" % (
            pair.large_size, pair.large_path,
            pair.small_size, pair.small_path)

    def finished(self):
        pass


class InteractiveBitTruncatedResolver(InteractiveResolver):
    def __init__(self, dry_run):
        InteractiveResolver.__init__(self, dry_run)

    def resolve(self, pair):
        progress = "[%d.%d/%d] " % (
            pair.ctxt_index+1, pair.ctxt_subindex+1, pair.ctxt_size)

        print "\n%sThe file '%s' is a shorter version of '%s'" % (
            progress, pair.small_path, pair.large_path)

        while True:
            print "Type 'd' to delete the shorter version. 's' to skip."

            input = raw_input("> ")
            if input == 'd':
                self._delete([pair.small_path])
                return
            elif input == 's':
                return
            else:
                continue

    def finished(self):
        pass


class ImageRelated(object):
    def __init__(self, path, max_image_size, background):
        self.path = path
        self.max_image_size = max_image_size
        self.file_size = os.path.getsize(path)
        self.image = Image.open(path)
        self.pixels = self.image.size[0] * self.image.size[1]
        self.bpp = self.file_size/float(self.pixels)
        self.scaled_image = self.scale(background)
        self.tk_image = ImageTk.PhotoImage(self.scaled_image)

    def scale(self, background):
        img = self.image
        size = img.size
        factor_x = self.max_image_size[0]/float(size[0])
        factor_y = self.max_image_size[1]/float(size[1])
        factor = min(factor_x, factor_y)
        if factor < 1:
            new_size = (int(size[0]*factor), int(size[1]*factor))
            img = img.resize(new_size)

        new = Image.new("RGB", self.max_image_size, background)
        width, height = img.size
        new.paste(img, (0, 0, width, height))
        assert new.size == self.max_image_size
        return new


def get_colors(cmp):
    base = "Black"
    better = "#008b00"

    if cmp == 0:
        return (base, base)
    elif cmp > 0:
        return (better, base)
    else:
        return (base, better)


def split_path(str):
    lines = []
    tmp = ""
    for i in str.split("/"):
        tmp += i+"/"
        if len(tmp) > 30:
            lines.append(tmp)
            tmp = ""
    if tmp:
        lines.append(tmp)
    return "\n".join(lines)[:-1]


def get_screen_size(root):
    return (root.winfo_screenwidth(), root.winfo_screenheight())


class CsvImageSimilarResolver(object):
    def __init__(self):
        print "similarity;path1;path2"

    # pylint: disable=R0201
    def resolve(self, pair):
        print "%f;%s;%s" % (
            pair.similarity,
            pair.path1,
            pair.path2)

    def finished(self):
        pass


class GuiImageSimilarResolver(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.root = Tk()
        self.root.bind('s', self.are_similar)
        self.root.bind('d', self.are_not_similar)
        self.root.bind('n', self.are_not_similar)
        self.root.bind('c', self.clear_feedback)
        self.root.bind('q', self.quit)
        self.root.bind('<Left>', self.goto_prev)
        self.root.bind('<Right>', self.goto_next)
        self.root.bind('f', self.toggle_skip)
        screen_size = get_screen_size(self.root)
        self.max_image_size = (int(0.4*screen_size[0]),
                               int(0.75*screen_size[1]))
        self.pairs = []
        self.item_frame = Frame(self.root)
        self.background = self.item_frame.cget("background")
        self.item_frame.pack(expand=False, side=TOP)

        self.skip_pairs_with_feedback = 1
        self.ref_counting = None
        self.label_sim = None
        self.label_bppl = self.label_bppr = None
        self.label_pixelsl = self.label_pixelsr = None
        self.label_resl = self.label_resr = None
        self.label_sizel = self.label_sizer = None
        self.label_pathl = self.label_pathr = None
        self.label_imgl = self.label_imgr = None
        self.create_gui()

        self.index = None

    def toggle_skip(self, *_):
        self.skip_pairs_with_feedback = not self.skip_pairs_with_feedback

    def goto_prev(self, *_):
        self.change_index(-1)

    def goto_next(self, *_):
        self.change_index(1)

    def are_similar(self, *_):
        self.save_feedback(1)

    def are_not_similar(self, *_):
        self.save_feedback(0)

    def clear_feedback(self, *_):
        self.pairs[self.index].clear_feedback()
        self.change_index(1)

    def save_feedback(self, are_similar):
        self.pairs[self.index].save_feedback(are_similar)
        self.change_index(1)

    def change_index(self, change):
        last_index = self.index
        while 1:
            self.index += change
            if self.index < 0:
                self.index = 0
            if self.index >= len(self.pairs):
                self.index = len(self.pairs)-1
            if self.index == last_index:
                break
            if not self.skip_pairs_with_feedback:
                break
            if not self.has_feedback():
                break
            last_index = self.index

        self.update_labels()

    def quit(self, _):
        self.root.destroy()

    def resolve(self, pair):
        self.pairs.append(pair)

    def finished(self):
        if self.pairs:
            self.index = 0
            self.update_labels()
            mainloop()
        else:
            print ("No duplicated images found. Maybe f_image.py was not run" +
                   " yet? Or there are no images in the path given.")

    def create_gui(self):
        root = self.item_frame

        row = 0

        self.label_sim = Label(root, text="no text (sim)")
        self.label_sim.grid(row=row, column=0, columnspan=2)
        row += 1

        self.label_imgl = Label(root, text="no image")
        self.label_imgl.grid(row=row, column=0)
        self.label_imgr = Label(root, text="no image")
        self.label_imgr.grid(row=row, column=1)
        row += 1

        self.label_pathl = Label(root, text="no text (path)")
        self.label_pathl.grid(row=row, column=0)
        self.label_pathr = Label(root, text="no text (path)")
        self.label_pathr.grid(row=row, column=1)
        row += 1

        self.label_sizel = Label(root, text="no text (size)")
        self.label_sizel.grid(row=row, column=0)
        self.label_sizer = Label(root, text="no text (size)")
        self.label_sizer.grid(row=row, column=1)
        row += 1

        self.label_pixelsl = Label(root, text="no text (pixels)")
        self.label_pixelsl.grid(row=row, column=0)
        self.label_pixelsr = Label(root, text="no text (pixels)")
        self.label_pixelsr.grid(row=row, column=1)
        row += 1

        self.label_resl = Label(root, text="no text (resolution)")
        self.label_resl.grid(row=row, column=0)
        self.label_resr = Label(root, text="no text (resolution)")
        self.label_resr.grid(row=row, column=1)
        row += 1

        self.label_bppl = Label(root, text="no text (bbp)")
        self.label_bppl.grid(row=row, column=0)
        self.label_bppr = Label(root, text="no text (bbp)")
        self.label_bppr.grid(row=row, column=1)
        row += 1

        Button(root, text="Similar images", underline=0,
               command=self.are_similar).grid(row=row, column=0)
        Button(root, text="Do not match (images are NOT similar)", underline=0,
               command=self.are_not_similar).grid(row=row, column=1)

    def has_feedback(self):
        pair = self.pairs[self.index]
        feedback = pair.get_feedback()
        return feedback is not None

    def update_labels(self):
        pair = self.pairs[self.index]
        feedback = pair.get_feedback()
        if feedback is None:
            feedback = "not yet"
            background = self.background
        elif feedback == 0:
            feedback = "not similar"
            background = "#FFE0E0"
        elif feedback == 1:
            feedback = "similar"
            background = "#E0FFE0"
        else:
            assert 0

        img1 = ImageRelated(pair.path1, self.max_image_size, background)
        img2 = ImageRelated(pair.path2, self.max_image_size, background)
        self.ref_counting = (img1, img2)

        self.item_frame.config(background=background)
        text = "%d/%d similarity=%f feedback = %s skip=%d" % (
            self.index+1, len(self.pairs),
            self.pairs[self.index].similarity, feedback,
            self.skip_pairs_with_feedback)
        self.label_sim.config(background=background, text=text)

        self.label_imgl.config(text=None, image=img1.tk_image)
        self.label_imgr.config(text=None, image=img2.tk_image)

        size1 = img1.file_size
        size2 = img2.file_size
        color1, color2 = get_colors(cmp(size1, size2))
        self.label_pathl.config(text=split_path(img1.path))
        self.label_pathr.config(text=split_path(img2.path))

        self.label_sizel.config(fg=color1, text=format_bytes(size1))
        self.label_sizer.config(fg=color2, text=format_bytes(size2))

        color1, color2 = get_colors(cmp(img1.pixels, img2.pixels))
        self.label_pixelsl.config(fg=color1, text=format_bytes(img1.pixels))
        self.label_pixelsr.config(fg=color2, text=format_bytes(img2.pixels))

        self.label_resl.config(fg=color1, text="%d x %d" % img1.image.size)
        self.label_resr.config(fg=color2, text="%d x %d" % img2.image.size)

        color1, color2 = get_colors(cmp(img1.bpp, img2.bpp))
        self.label_bppl.config(fg=color1, text="%f" % img1.bpp)
        self.label_bppr.config(fg=color2, text="%f" % img2.bpp)


def main():
    parser = argparse.ArgumentParser(
        description='Find files with equal or similar content.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to scan for duplicate files " +
                        "(if not given '.' will be used)")
    add_common_command_line_arguments(parser)
    parser.add_argument('-c', '--csv', action="store_true",
                        help='print all findings as a CSV using instead ' +
                        'of resolve interactive')
    parser.add_argument('-n', '--dry-run', action="store_true", dest='dry_run',
                        help='do not delete any files')
    parser.add_argument('-t', '--truncated', action="store_true",
                        dest='truncated',
                        help='search for truncated files')
    parser.add_argument('-i', '--image', action="store_true",
                        dest='image',
                        help='search for similar images')
    parser.add_argument('-s', '--min-similarity',
                        default=0.9,
                        help='require at least this image similarity')
    parser.add_argument('-S', '--image-signature',
                        default=1,
                        help="Image signature to use. Valid is '1' and '2'.")

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    if args.image:
        if args.csv:
            resolver = CsvImageSimilarResolver()
        else:
            resolver = GuiImageSimilarResolver(args.dry_run)
        finder = ImageSimilarFinder(repo, args.roots,
                                    int(args.image_signature))
        found_items = finder.find(float(args.min_similarity))
    elif args.truncated:
        if args.csv:
            resolver = CsvBitTruncatedResolver()
        else:
            resolver = InteractiveBitTruncatedResolver(args.dry_run)
        finder = BitTruncatedFinder(repo, args.roots)
        found_items = finder.find()
    else:
        if args.csv:
            resolver = CsvBitEqualResolver()
        else:
            resolver = InteractiveBitEqualResolver(args.dry_run)
        finder = BitEqualFinder(repo, args.roots)
        found_items = finder.find()

    for item in found_items:
        resolver.resolve(item)
    resolver.finished()

if __name__ == '__main__':
    main()
