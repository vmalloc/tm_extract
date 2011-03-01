#! /usr/bin/python
import shutil
import argparse
import os

def extract(args):
    dest_path = args.dest
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        shutil.copymode(args.root, dest_path)
    if not os.path.isdir(dest_path):
        raise Exception("Destination %s does not exist" % dest_path)
    for physical_path, virtual_path in _walk_paths(args.root):
        _extract_single(physical_path, virtual_path, args)

def _walk_paths(physical_path, virtual_path=None):
    cache_dir = _find_cache_dir(physical_path)

    if virtual_path is None:
        virtual_path = physical_path

    return _traverse_path(physical_path, virtual_path, cache_dir)
    
def _find_cache_dir(root):
    if not os.path.isdir(root):
        root = os.path.basename(root)
    cached_dir_name = ".HFS+ Private Directory Data\r"
    root_inode = os.stat("/").st_ino
    while not os.path.exists(os.path.join(root, cached_dir_name)):
        root = os.path.abspath(os.path.join(root, ".."))
        if os.stat(root).st_ino == root_inode:
            raise Exception("Cannot find cache dir")
    return os.path.join(root, cached_dir_name)

def _traverse_path(physical_path, virtual_path, cached_dir):
    for path, dirnames, filenames in os.walk(physical_path):
        for filename in filenames:
            file_path = os.path.join(path, filename)
            relative_file_path = os.path.relpath(file_path, physical_path)
            vpath = os.path.join(virtual_path, relative_file_path)
            ppath = os.path.join(physical_path, relative_file_path)
            link_id = _get_link_id(filename)
            if link_id is None:
                yield ppath, vpath
            else:
                ppath = os.path.join(cached_dir, "dir_%s" % link_id)
                for x in _traverse_path(ppath, vpath, cached_dir):
                    yield x

def _get_link_id(filename):
    stat_info = os.stat(filename)
    if stat_info.st_links <= 127:
        return None
    return stat_info.st_links
    
def _extract_single(physical_path, virtual_path, args):
    rel_path = os.path.relpath(virtual_path, args.root)
    dest_path = os.path.join(args.dest, rel_path)
    if os.path.isdir(physical_path):
        raise NotImplementedError()
    dest_dir = os.path.dirname(dest_path)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
        shutil.copymode(os.path.dirname(physical_path), dest_dir)
    shutil.copy2(physical_path, dest_path)
     

parser = argparse.ArgumentParser()
parser.add_argument("root")
parser.add_argument("dest")

if __name__ == "__main__": 
    args = parser.parse_args()
    extract(args)
