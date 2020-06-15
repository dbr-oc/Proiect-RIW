import os


def ensure_path(parent_dir, scheme, dir_queue):
    if not os.path.isdir(parent_dir + "/" + scheme):
        os.mkdir(parent_dir + "/" + scheme)
    for i in range(len(dir_queue)):
        d = parent_dir + "/" + scheme + "/" + "/".join(dir_queue[:i + 1])
        if not os.path.isdir(d):
            os.mkdir(d)
    return parent_dir + "/" + scheme + "/" + "/".join(dir_queue)
