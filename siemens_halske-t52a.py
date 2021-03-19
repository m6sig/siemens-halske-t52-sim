#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2021, M6SIG

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Siemens & Halske SFM T52a Cipher Machine simulator
#

import sys
import textwrap
import argparse
from pathlib import Path
import random
randgen = random.SystemRandom()

'''ASCII/TTY coding conversion data.'''

# Constants for asc2tty array
INVC   = 255    # invalid character mapping
FIGS_F = 128    # figures required flag
ETHR_F = 64     # valid in either shift
LTRS   = 31     # letters shift character
FIGS   = 27     # figures shift character
MSX5   = 31     # mask off 5 LSBs
MSX7   = 127    # mask off 7 LSBs

# For converting ASCII to 5-bits TTY code.
#
# 5 LSBs are significant.
# Bit 7 set if figures shift required.
# 0xff indicates invalid character mapping.
# Lower-case mapped to upper-case
#
# Dollor  $  represents "WHO ARE YOU" 
# Tilda  (~) represents "Bell"
asc2tty = [ 
# NUL                                       \a
  64, INVC, INVC, INVC, INVC, INVC, INVC,  154, INVC, INVC,
# \n                \r
  72, INVC, INVC,   66, INVC, INVC, INVC, INVC, INVC, INVC,
INVC, INVC, INVC, INVC, INVC, INVC, INVC, INVC, INVC, INVC,
#             ' '    !     "     #     $     %     &     '
INVC, INVC,   68, INVC, INVC, INVC,  146, INVC, INVC,  148,
#  (     )     *     +     ,     -     .     /
 158,  137, INVC,  145,  134,  152,  135,  151,
# 0     1    2    3    4    5    6    7    8    9    :     
 141, 157, 153, 144, 138, 129, 149, 156, 140, 131, 142,
#  ;    <    =    >    ?    @   A   B   C   D   E   F   G
INVC, 158, 143, 137, 147,INVC, 24, 19, 14, 18, 16, 22, 11,
# H   I   J   K  L  M  N   O   P  Q   R   S  T   U   V   W
  5, 12, 26, 30, 9, 7, 6, 3, 13, 29, 10, 20, 1, 28, 15, 25,
# X   Y   Z    [     \    ]     ^     _     `   a   b   c
 23, 21, 17, 158, INVC, 137, INVC, INVC, INVC, 24, 19, 14,
# d   e   f   g  h   i   j   k  l  m  n   o  p   q   r   s
 18, 16, 22, 11, 5, 12, 26, 30, 9, 7, 6, 3, 13, 29, 10, 20,
# t   u   v   w   x   y   z    {     |    }    ~   DEL
  1, 28, 15, 25, 23, 21, 17, 158, INVC, 137, 154, INVC]

# For converting 5-bits TTY code to ASCII.
tty_ltrs2asc = [
    '\x00', 'T', '\x0D',  'O', ' ', 'H', 'N', 'M',
    '\x0A', 'L',    'R',  'G', 'I', 'P', 'C', 'V',
       'E', 'Z',    'D',  'B', 'S', 'Y', 'F', 'X',
       'A', 'W',    'J', FIGS, 'U', 'Q', 'K', LTRS]

tty_figs2asc = [
    '\x00', '5', '\x0D',  '9', ' ', '&', ',', '.',
    '\x0A', ')',    '4',  '&', '8', '0', ':', '=',
       '3', '+',    '$',  '?', "'", '6', '&', '/',
       '-', '2', '\x07', FIGS, '7', '1', '(', LTRS]

def ascii2tty(s):
    '''Convert from ASCII to 5-bits TTY code.

    Assumes reader may initially be in either letters or figures
    shift, and emits a shift char prior to first output char that
    is not valid in either shift.'''

    figs = False
    result = []
    # Emit initial shift if needed
    if len(s) > 0:
        char = asc2tty[s[0] & MSX7]
        if (char & ETHR_F):
            # Valid in either shift
            pass
        elif (char & FIGS_F):
            # Must be in figures shift
            result.append(chr(FIGS))
            figs = True
        else:
            # Must be in letters shift
            result.append(chr(LTRS))
            figs = False
    
    # Convert chars
    for char in s:
        # Drop MSB and convert
        char = asc2tty[char & MSX7]

        # Convert if valid
        if char != INVC:

            # Emit shift char if needed
            if (char & ETHR_F):
                # Valid in either shift
                pass
            elif (char & FIGS_F):
                # Must be in figures shift
                if figs is not True:
                    # Not already in figures shift
                    # i.e. either in letters shift or indeterminate
                    result.append(chr(FIGS))
                    figs = True
            elif figs is not False:
                # In figures or indeterminate shift, but must be in letter shift
                result.append(chr(LTRS))
                figs = False

            # Emit the converted char
            result.append(chr(char & MSX5))

    return ''.join(result)


def tty2ascii(s):
    '''Convert from 5-level TTY code to ASCII.

    Assumes initial letters shift state.'''

    figs = False
    result = []
    for char in s:
        char = ord(char) & MSX5
        if char == LTRS:
            figs = False
        elif char == FIGS:
            figs = True
        else:
            if figs:
                char = tty_figs2asc[char]
            else:
                char = tty_ltrs2asc[char]
            result.append(char)

    return ''.join(result)


class Wheel:
    """ Class representing a specific wheel. """

    def __init__(self, wheel_data, initial):
        self.wheel_data = wheel_data
        self.wheel_size = len(wheel_data)
        self.state = initial

    def advance(self):
        self.state = (self.state + 1) % self.wheel_size

    def get_val(self):
        return self.wheel_data[self.state]


class WheelBank:
    """ Class for a bank of wheels. """

    def __init__(self, wheels):
        self.wheels = wheels

    def advance(self):
        for w in self.wheels:
            w.advance()

    def get_val(self):
        result = []
        for i in range(5):
            result.append(self.wheels[i].get_val())
        # Wheel numbered 1 is low bit, so we need to flip the bit order.
        # NOTE: I'm not 100% sure which wheel has the MSB and which the
        # LSB. Would be nice to confirm this better. Diagrams seem to show
        # wheel X1, for example, on input 1. And a Baudot code chart nearby
        # shows bit #1 as LSB. So I think this is right...
        return int("0b" + ''.join([str(i) for i in result[::-1]]), 2)


class SFM_T52a:
    """ Represents an instance of a Siemens & Halske T52a Cipher Machine. """

    def __init__(self, X, S, initial=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]):
        self.X_wheels = WheelBank([Wheel(data, i)
                                   for data, i in zip(X, initial[:5])])
        self.S_wheels = WheelBank([Wheel(data, i)
                                   for data, i in zip(S, initial[5:])])

    def advance(self):
        """ Advances the wheels. Should be called after every encrypt or
            decrypt.
        """
        # All wheel advance every time
        self.X_wheels.advance()
        self.S_wheels.advance()

    def encrypt_char(self, c):
        """ Encrypt a single character. Expects an ordinal of the
            character.
        """

        result = '{:05b}'.format(c ^ self.X_wheels.get_val())

        # Swap operation
        if (self.S_wheels.get_val()>>4)&1:
            result = result[4:] + result[1:4] + result[:1]
        if (self.S_wheels.get_val()>>3)&1:
            result = result[:3] + result[3:5][::-1]
        if (self.S_wheels.get_val()>>2)&1:
            result = result[:2] + result[2:4][::-1] + result[4:]
        if (self.S_wheels.get_val()>>1)&1:
            result = result[:1] + result[1:3][::-1] + result[3:]
        if self.S_wheels.get_val()&1:
            result = result[:2][::-1] + result[2:]

        self.advance()
        return int(result, 2)

    def decrypt_char(self, c):
        """ Decrypt a single character. Expects an ordinal of the
            character.
        """

        # Reverse swap operation
        result = '{:05b}'.format(c)
        if self.S_wheels.get_val()&1:
            result = result[:2][::-1] + result[2:]
        if (self.S_wheels.get_val()>>1)&1:
            result = result[:1] + result[1:3][::-1] + result[3:]
        if (self.S_wheels.get_val()>>2)&1:
            result = result[:2] + result[2:4][::-1] + result[4:]
        if (self.S_wheels.get_val()>>3)&1:
            result = result[:3] + result[3:5][::-1]
        if (self.S_wheels.get_val()>>4)&1:
            result = result[4:] + result[1:4] + result[:1]

        result = int(result, 2) ^ self.X_wheels.get_val()
        self.advance()
        return result

    def encrypt(self, m):
        """ Encrypt/decrypt a message string. Uses Baudot encoding. """

        return ''.join([chr(self.encrypt_char(ord(c))) for c in m])

    def decrypt(self, m):
        """ Encrypt/decrypt a message string. Uses Baudot encoding. """

        return ''.join([chr(self.decrypt_char(ord(c))) for c in m])


def write_keyfile(output_file, X_sizes, S_sizes,
                      X_wheels, S_wheels, indicator):
    with open(output_file, 'w') as f_out:
        f_out.write("# Number of teeth on each wheel for xor operation:\n")
        f_out.write("X_sizes = %s\n" % str(X_sizes))
        f_out.write("# Number of teeth on each wheel for swap operation:\n")
        f_out.write("S_sizes = %s\n" % str(S_sizes))
        f_out.write("\n# Settings for the wheels:\n")
        f_out.write("X_wheels = %s\n" % str(X_wheels))
        f_out.write("S_wheels = %s\n" % str(S_wheels))
        f_out.write("\n# Indicator represents the start positions of the wheels, in "\
                "this order:\n")
        f_out.write("# [xor_1, xor_2, xor_3, xor_4, xor_5, swap_1, swap_2, swap_3, swap_4, swap_5]\n")
        f_out.write("indicator = %s\n\n" % str(indicator))


class gather_args(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not 'arg_sequence' in namespace:
            setattr(namespace, 'arg_sequence', [])
        prev = namespace.arg_sequence
        prev.append((self.dest, values))
        setattr(namespace, 'arg_sequence', prev)


def validate_args(infile):
    if not infile.is_file():
        sys.exit('"{}" is not a file.'.format(infile))


# Main entry point when called as an executable script.
if __name__ == '__main__':

    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        prog='python3 siemens_halske-t52a.py',
        epilog=textwrap.dedent('''\
        Example:
          python3 siemens_halske-t52a.py --keygen <key file>
          python3 siemens_halske-t52a.py --encrypt <input file> <key file> <output file>
          python3 siemens_halske-t52a.py --decrypt <input file> <key file> <output file>
          python3 siemens_halske-t52a.py --readtape <input file>
          '''),
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    # maincommandoption = parser.add_mutually_exclusive_group()
    parser.add_argument('--keygen', action=gather_args, nargs=1,
                        metavar='<key file>',
                        help='''Creates a random key file with normal SZ40 teeth counts and sets random indicators. Edit the file to suit.''')

    parser.add_argument('--encrypt', action=gather_args, nargs=3,
                        metavar=('<input file>', '<key file>', '<output file>'),
                        help='''Encode ASCII plaintext to Baudot code (5 bits per byte) and encrypt with wheel settings in key file, writing ciphertext to output file.''')

    parser.add_argument('--decrypt', action=gather_args, nargs=3,
                        metavar=('<input file>', '<key file>', '<output file>'),
                        help='''Decrypt the input file with wheel settings in key file, decode from Baudot code and and output ASCII plaintext to output file.''')

    parser.add_argument('--readtape', action=gather_args, nargs=1,
                        metavar='<input file>',
                        help='''Read input file in Baudot code and display ASCII equivalent.''')


    # Parse the command-line arguments. Need to create empty arg_sequence
    # in case no command-line arguments were included.
    args = parser.parse_args()
    if not 'arg_sequence' in args:
        setattr(args, 'arg_sequence', [])
    cmd = ''
    opt = ''


    if len(args.arg_sequence) == 1:
        cmd = args.arg_sequence[0][0]
        opt = args.arg_sequence[0][1]
    else:
        sys.stderr.write("Wrong options!\npython3 siemens_halske-t52a.py --help or -h for usage info.\n")
        exit(1)


    if cmd == 'keygen':
        key_file = opt[0]

        # Arranging wheel order.
        X_sizes = []
        S_sizes = []
        Wheel_Size = [73, 71, 69, 67, 65, 64, 61, 59, 53, 47]
        randgen.shuffle(Wheel_Size)
        randgen.shuffle(Wheel_Size)
        randgen.shuffle(Wheel_Size)
        for i in range(5):
            X_sizes.append(Wheel_Size.pop())
            S_sizes.append(Wheel_Size.pop())

        keygen_randombuf = '{:0700b}'.format(randgen.getrandbits(700))
        X_wheels = [[], [], [], [], []]
        S_wheels = [[], [], [], [], []]
        indicator = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,]
        for i in range(5):
            X_wheels[i] = list(map(int, list(keygen_randombuf[:X_sizes[i]])))
            keygen_randombuf = keygen_randombuf[X_sizes[i]:]
            indicator[i] = int(keygen_randombuf[:7], 2) % X_sizes[i]
            keygen_randombuf = keygen_randombuf[7:]
        for i in range(5):
            S_wheels[i] = list(map(int, list(keygen_randombuf[:S_sizes[i]])))
            keygen_randombuf = keygen_randombuf[S_sizes[i]:]
            indicator[i + 5] = int(keygen_randombuf[:7], 2) % S_sizes[i]
            keygen_randombuf = keygen_randombuf[7:]
        write_keyfile(key_file, X_sizes, S_sizes, X_wheels, S_wheels, indicator)
        print("New key data written to:", key_file)


    elif cmd == 'encrypt':
        input_file = Path(opt[0])
        key_file = Path(opt[1])
        output_file = opt[2]
        validate_args(input_file)
        validate_args(key_file)
        with key_file.open('r') as key_file_contents:
            exec(key_file_contents.read())
        input_ascii = []
        with input_file.open('rb') as f_input:
            while f_input.peek():
                input_ascii.append(ord(f_input.read(1)))

        input_baudot = ascii2tty(input_ascii)

        print("Encrypting...")
        cipher = SFM_T52a(X_wheels, S_wheels, indicator)

        ciphertext = cipher.encrypt(input_baudot)

        with open(output_file, 'w') as f_out:
            f_out.write(ciphertext)
        print("Encrypted message written to:", output_file)


    elif cmd == 'decrypt':
        input_file = Path(opt[0])
        key_file = Path(opt[1])
        output_file = opt[2]
        validate_args(input_file)
        validate_args(key_file)
        with open(key_file, 'r') as key_file_contents:
            exec(key_file_contents.read())
        input_ciphertext = []
        with input_file.open('rb') as f:
            while f.peek():
                input_ciphertext.append(f.read(1))

        print("Decrypting...")

        cipher = SFM_T52a(X_wheels, S_wheels, indicator)

        plaintext_stream = cipher.decrypt(input_ciphertext)

        plaintext_ascii = tty2ascii(plaintext_stream)

        with open(output_file, 'w') as f_out:
            f_out.write(plaintext_ascii)
        print("Decrypted message written to:", output_file)


    elif cmd == 'readtape':
        tty_file = Path(opt[0])
        validate_args(tty_file)
        print("Reading TTY tape file...")
        with open(tty_file, 'r') as f_in:
            tty_stream = f_in.read()
        print(tty2ascii(tty_stream))


    else:
        sys.stderr.write("Wrong options!\npython3 siemens_halske-t52a.py --help or -h for usage info.\n")
        exit(1)
