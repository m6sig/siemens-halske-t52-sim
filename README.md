# siemens-halske-t52-sim
A simulator for the Siemens &amp; Halske Schl├╝sselfernschreibmaschine T52 Teleprinter-cipher all in one machine written in Python3.

This project is to all crypto analyser and breaker who broke them during the WW2.

## Available model
`siemens_halske-t52a.py`:  Siemens &amp; Halske SFM T52a

## Note
There are two things that differ from the real machine:
1. Wheel order and indicator layout generated by the `--keygen` option is not in the `A B C D E F G H I K` order but in teleprinter bits stream order, xor function followed by swap function instead.
2. It is very diffcult to change the order and purpose of generated wheel setting file. In the real machine you just need to reconnect those jumper.
BTW: All wheels are from facture and not designed to be rewired by user. But wheel settings can be customised.

## Usage
```
$ python3 siemens_halske-t52a.py [-h] [--keygen <key file>]
                                      [--encrypt <input file> <key file> <output file>]
                                      [--decrypt <input file> <key file> <output file>]
                                      [--readtape <input file>]

optional arguments:
  -h, --help            show this help message and exit
  --keygen <key file>   Creates a random key file with normal SZ40 teeth
                        counts and sets random indicators. Edit the file to
                        suit.
  --encrypt <input file> <key file> <output file>
                        Encode ASCII plaintext to Baudot code (5 bits per
                        byte) and encrypt with wheel settings in key file,
                        writing ciphertext to output file.
  --decrypt <input file> <key file> <output file>
                        Decrypt the input file with wheel settings in key
                        file, decode from Baudot code and and output ASCII
                        plaintext to output file.
  --readtape <input file>
                        Read input file in Baudot code and display ASCII
                        equivalent.

Example:
  python3 siemens_halske-t52a.py --keygen <key file>
  python3 siemens_halske-t52a.py --encrypt <input file> <key file> <output file>
  python3 siemens_halske-t52a.py --decrypt <input file> <key file> <output file>
  python3 siemens_halske-t52a.py --readtape <input file>
```
