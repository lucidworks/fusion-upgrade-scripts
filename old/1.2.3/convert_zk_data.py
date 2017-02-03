
# TODO: Write a script to update backend ZK data and call it from here

import json
import argparse

from convert_users_roles_realms import read_convert_dump_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the ZK data for new version")
    parser.add_argument('zkdump_filename', type=str, help="The ZK dump file")
    parser.add_argument('introspect_filename', type=str, help="File name of the introspect")
    parser.add_argument('output_filename', type=str, help="Output dump file name")

    args = parser.parse_args()
    read_convert_dump_file(args.zkdump_filename, args.introspect_filename, args.output_filename)
