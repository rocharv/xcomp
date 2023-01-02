#!/usr/bin/env python3
import argparse
from os import path
from os import walk
from pathlib import Path
from re import search
from xxhash import xxh64


def xxh3(file_name: str) -> str:
    if path.exists(file_name):
        hash_object = xxh64()
        with open(file_name, "rb") as f:
            for chunk in iter(lambda: f.read(1024), b""):
                hash_object.update(chunk)
        return hash_object.hexdigest()
    else:
        print(f"the target path doesn't exist: {file_name}")
        raise SystemExit(1)


def read_arguments():
    arg_parser = argparse.ArgumentParser(
        prog="xcomp",
        description=("Compare two paths using xxh3 hash algorithm. "
                     "Paths must be both files or both directories."),
        epilog="written by Rodrigo Viana Rocha"
    )

    arg_parser.add_argument(
        "path1",
        help="can be a path to a file or a directory"
    )

    arg_parser.add_argument(
        "path2",
        help="can be a path to a file or a directory"
    )

    arg_parser.add_argument(
        "-c",
        "--cache_file",
        action="append",
        help=("use one or more plain text files as cache for the "
              "file hash computation. All lines in the cache file(s) should "
              "like: d50463dd92503d34 '/path/to/file'")
    )

    arg_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help=("compare recursively every file belonging to each path provided"
              "(and its subdirectories) with each other. "
              "Both paths must be directories")
    )

    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show the hexdigest and respective full path of each file"
    )

    args = arg_parser.parse_args()
    return args


def load_hash_cache(args) -> dict[str, str]:
    hash_cache: dict[str, str] = {}
    at_least_one_match = False

    for file in args.cache_file:
        full_file_path = Path(file)
        if not full_file_path.exists():
            print(f"xcomp: the cache file ({file}) doesn't exist")
            raise SystemExit(1)
        file_object = open(full_file_path, "rt")
        for line in file_object:
            match = search("([a-f0-9]{16})[ \t]+'?([^'\n]+)'?", line)
            if match:
                at_least_one_match = True
                hash_cache[path.abspath(match.group(2))] = match.group(1)

    if not at_least_one_match:
        print(
            (f"xcomp: the cache file ({file}) doesn't comply with "
                "format requirements")
        )
        raise SystemExit(1)

    return hash_cache


def get_hash_dict(directory_path: str, args) -> dict[str, list[str]]:
    result_dict: dict[str, list[str]] = {}
    hash_cache: dict[str, str] = {}

    if args.cache_file:
        hash_cache = load_hash_cache(args)

    for current_directory, _, file_names in walk(directory_path):
        for file_name in file_names:
            file_full_path = path.abspath(
                path.join(current_directory, file_name))

            if file_full_path in hash_cache:
                hash = hash_cache[file_full_path]
                if args.verbose:
                    print(f"{hash} '{file_full_path}' cached")
            else:
                hash = xxh3(file_full_path)
                if args.verbose:
                    print(f"{hash} '{file_full_path}'")

            if hash in result_dict:
                result_dict[hash].append(file_full_path)
            else:
                result_dict[hash] = [file_full_path]

        if not args.recursive:
            return result_dict

    return result_dict


def show_file_comparison(args) -> None:
    hash1: str = xxh3(args.path1)
    hash2: str = xxh3(args.path2)

    if args.verbose:
        print(f"{hash1} '{path.abspath(args.path1)}'")
        print(f"{hash2} '{path.abspath(args.path2)}'")

    if hash1 == hash2:
        if args.path1 != args.path2:
            print(
                (f"={hash1} ['{path.abspath(args.path1)}', "
                 f"'{path.abspath(args.path2)}']")
            )

        print("=input files are redundant")
        return
    else:
        print(f"<{hash1} '{path.abspath(args.path1)}'")
        print(f">{hash2} '{path.abspath(args.path2)}'")
        raise SystemExit(1)


def show_directory_comparison(args) -> None:
    content_redundancy: bool = True
    dict_path1: dict[str, list[str]] = get_hash_dict(args.path1, args)
    dict_path2: dict[str, list[str]] = get_hash_dict(args.path2, args)

    for key in dict_path1:
        if len(dict_path1[key]) > 1:
            print("{" + f"{key} {dict_path1[key]}")

    for key in dict_path2:
        if len(dict_path2[key]) > 1:
            print("}" + f"{key} {dict_path2[key]}")

    for key in dict_path1:
        if key not in dict_path2:
            content_redundancy = False
            for not_redundant_file in dict_path1[key]:
                print(f"<{key} '{not_redundant_file}'")

    for key in dict_path2:
        if key not in dict_path1:
            content_redundancy = False
            for not_redundant_file in dict_path2[key]:
                print(f">{key} '{not_redundant_file}'")
        else:
            print(f"={key} {dict_path1[key] + dict_path2[key]}")

    if content_redundancy:
        print("=input directories are redundant")


def main(args=None) -> None:
    if not args:
        args = read_arguments()

    if path.isfile(args.path1) and path.isfile(args.path2):
        show_file_comparison(args)

    elif path.isdir(args.path1) and path.isdir(args.path2):
        show_directory_comparison(args)

    elif (not path.exists(args.path1) or not path.exists(args.path2)):
        if not path.exists(args.path1):
            print(f"xcomp: the path '{args.path1}' doesn't exist")
        if not path.exists(args.path2):
            print(f"xcomp: the path '{args.path2}' doesn't exist")
        raise SystemExit(1)

    elif path.isfile(args.path1) and path.isdir(args.path2):
        print(
            (f"xcomp: can't compare a single file ({args.path1}) with "
             f"a directory ({args.path2})")
        )
        raise SystemExit(1)

    elif path.isdir(args.path1) and path.isfile(args.path2):
        print(
            (f"xcomp: can't compare a directory ({args.path1}) with "
             f"a single file ({args.path2})")
        )
        raise SystemExit(1)


if __name__ == '__main__':
    main()
