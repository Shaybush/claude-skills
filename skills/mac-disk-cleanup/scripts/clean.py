#!/usr/bin/env python3
import argparse
import os
import shutil
import sys

DEPENDENCY_TARGETS = ['node_modules', '.venv', 'venv']
BUILD_TARGETS = ['__pycache__', '.next', '.nuxt', '.turbo', '.parcel-cache', '.pytest_cache', '.mypy_cache', 'dist', 'build', 'target']
NEVER_DESCEND = ['.git', 'Library', 'Applications', '.Trash']


def human(num_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f'{num_bytes:.1f} {unit}'
        num_bytes /= 1024.0
    return f'{num_bytes:.1f} PB'


def disk_usage(path, counted_inodes):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path, onerror=lambda err: None):
        for name in dirnames + filenames:
            try:
                info = os.lstat(os.path.join(dirpath, name))
            except OSError:
                continue
            if info.st_nlink > 1:
                key = (info.st_dev, info.st_ino)
                if key in counted_inodes:
                    continue
                counted_inodes.add(key)
            total += info.st_blocks * 512
    return total


def find_targets(root, target_names):
    found = []
    for dirpath, dirnames, _ in os.walk(root, topdown=True, onerror=lambda err: None):
        for name in [d for d in dirnames if d in target_names]:
            found.append(os.path.join(dirpath, name))
        dirnames[:] = [d for d in dirnames if d not in target_names and d not in NEVER_DESCEND]
    return found


def main():
    parser = argparse.ArgumentParser(
        description='Find and remove regenerable dependency and build directories (node_modules, .venv, ...).')
    parser.add_argument('root', nargs='?', default='.',
                        help='directory tree to scan (default: current directory)')
    parser.add_argument('--dry-run', action='store_true',
                        help='report what would be removed without deleting anything')
    parser.add_argument('--include-build', action='store_true',
                        help=f'also target build output: {", ".join(BUILD_TARGETS)}')
    parser.add_argument('--min-mb', type=float, default=0.0,
                        help='ignore directories smaller than this many MB')
    parser.add_argument('--top', type=int, default=15,
                        help='how many of the largest directories to list (default: 15)')
    args = parser.parse_args()

    root = os.path.expanduser(args.root)
    if not os.path.isdir(root):
        print(f'error: {root} is not a directory', file=sys.stderr)
        return 1

    target_names = set(DEPENDENCY_TARGETS)
    if args.include_build:
        target_names.update(BUILD_TARGETS)

    print(f'scanning {root} for {", ".join(sorted(target_names))} ...', flush=True)
    paths = find_targets(root, target_names)
    if not paths:
        print('nothing found')
        return 0

    counted_inodes = set()
    sized = []
    for path in paths:
        size = disk_usage(path, counted_inodes)
        if size >= args.min_mb * 1024 * 1024:
            sized.append((size, path))
    sized.sort(reverse=True)

    if not sized:
        print(f'found {len(paths)} directories, none at or above {args.min_mb} MB')
        return 0

    total = sum(size for size, _ in sized)
    print(f'\nlargest {min(args.top, len(sized))} of {len(sized)}:')
    for size, path in sized[:args.top]:
        print(f'  {human(size):>10}  {path}')

    verb = 'would free' if args.dry_run else 'freeing'
    print(f'\n{verb} {human(total)} across {len(sized)} directories')

    if args.dry_run:
        print('\ndry run: nothing deleted. re-run without --dry-run to remove.')
        return 0

    removed = 0
    failed = []
    for _, path in sized:
        try:
            shutil.rmtree(path)
            removed += 1
        except OSError as err:
            failed.append((path, err))

    print(f'removed {removed} directories')
    if failed:
        print(f'\n{len(failed)} could not be removed:')
        for path, err in failed[:10]:
            print(f'  {path}: {err}')
    print('\nnote: pnpm hardlinks node_modules into its content-addressable store.')
    print('run "pnpm store prune" afterwards to release the store copies too.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
