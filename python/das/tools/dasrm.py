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
    parser.add_argument("keys", metavar="key", nargs="*", default=[])
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input

    try:
        data = das.read(args.input)
    except Exception as e:
        sys.stderr.write("Failed to read file '%s' (%s)\n" % (e, args.input))
        return 1

    orgdata = das.copy(data)

    for key in args.keys:
        try:
            das.cli.remove(data, key)
        except Exception as e:
            sys.stderr.write("Failed to remove field '%s' (%s)\n" % (key, e))
            continue

    if data != orgdata:
        if not args.dryrun:
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
