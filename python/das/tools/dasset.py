import os
import sys
import argparse
import das
import das.cli


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file path", required=True)
    parser.add_argument("-o", "--output", help="Output file path (input file if not set)")
    parser.add_argument(
        "-ov", "--overwrite", help="Overwrite existing output file", action="store_true"
    )
    parser.add_argument("-dr", "--dry-run", help="Don't do anything", action="store_true")
    parser.add_argument(
        "keyvals", nargs="*", metavar="key val", default=[], action=das.cli.StorePairs
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input

    try:
        data = das.read(args.input)
    except Exception as e:
        sys.stderr.write("Failed to read file '%s' (%s)\n" % (e, args.input))
        return 1

    orgdata = das.copy(data)

    for key, val in args.keyvals:
        try:
            das.cli.set(data, key, val)
        except Exception as e:
            sys.stderr.write("Failed to set value for field '%s' (%s)\n" % (key, e))
            continue

    if data != orgdata:
        if not args.dry_run:
            if os.path.isfile(args.output) and not args.overwrite:
                sys.stderr.write("Output file already exists\n")
                return 1
            try:
                das.write(data, args.output)
            except Exception as e:
                sys.stderr.write("Failed to write file '%s' (%s)\n" % (args.output, e))
                return 1
        else:
            das.pprint(data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
