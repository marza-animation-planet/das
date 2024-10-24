import sys
import argparse
import das
import das.cli


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file path", required=True)
    parser.add_argument("-pp", "--pretty-print", action="store_true")
    parser.add_argument("keys", metavar="key", nargs="*", default=[])
    args = parser.parse_args()

    vals = []
    try:
        data = das.read(args.input)
    except Exception as e:
        sys.stderr.write("Failed to read file '%s' (%s)\n" % (e, args.input))
        return 1

    for key in args.keys:
        try:
            vals.append(das.cli.get(data, key))
        except Exception as e:
            sys.stderr.write("Failed to get value for field '%s' (%s)\n" % (key, e))
            vals.append(None)

    if len(args.keys) == 1:
        vals = vals[0]

    if args.pretty_print:
        das.pprint(vals)
    else:
        print(vals)

    return 0

if __name__ == "__main__":
    sys.exit(main())
