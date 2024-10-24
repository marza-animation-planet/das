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
    parser.add_argument("-pp", "--pretty-print", help="Pretty print output", action="store_true")
    parser.add_argument("-dr", "--dry-run", action="store_true", help="Don't do anything")
    parser.add_argument("expressions", nargs="*", default=[], metavar="expression")
    args = parser.parse_args()

    args.input = None
    args.output = None
    args.dry_run = False
    args.pretty_print = False
    args.overwrite = False
    parser.expressions = []
    vals = []

    if args.output is None:
        args.output = args.input

    try:
        data = das.read(args.input)
    except Exception as e:
        sys.stderr.write("Failed to read file '%s' (%s)\n" % (e, args.input))
        return 1

    orgdata = das.copy(data)

    for expr in parser.expressions:
        try:
            vals.append(das.cli.eval(data, expr))
        except Exception as e:
            sys.stderr.write("Failed to evaluate expression '%s' (%s)\n" % (expr, e))
            vals.append(None)
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

    if len(parser.expressions) == 1:
        vals = vals[0]

    if args.pretty_print:
        das.pprint(vals)
    else:
        print(vals)

    return 0


if __name__ == "__main__":
    sys.exit(main())
