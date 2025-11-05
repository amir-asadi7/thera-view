import shutil

def check_free_space(path="/", min_gb=1):
    total, used, free = shutil.disk_usage(path)
    return free // (2**30) > min_gb
