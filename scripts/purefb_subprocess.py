#!/usr/bin/env python3
import os
import subprocess

class PureSubprocessor:
    def __init__(self, filesystem, src_ip, dest_ip):
        self.filesystem = filesystem
        self.src_ip = src_ip
        self.src_export = f"{src_ip}:/{filesystem}"
        self.src_mount = f"/mnt/pure_migration/{filesystem}_src/"
        self.dest_ip = dest_ip
        self.dest_export = f"{dest_ip}:/{filesystem}"
        self.dest_mount = f"/mnt/pure_migration/{filesystem}_dest/"

    # Make directories for mount points
    def mkdir(self, src=True, dest=True):
        if src:
            os.makedirs(self.src_mount, exist_ok=True)
        if dest:
            os.makedirs(self.dest_mount, exist_ok=True)

    # Mount NFS filesystems onto mount points
    def mount(self, src=True, dest=True):
        if src:
            if subprocess.run(["mountpoint", "-q", self.src_mount]).returncode == 0:
                print(f"{self.src_mount} : Already Mounted")
                print()
            else:
                subprocess.run(["mount", "-t", "nfs", self.src_export, self.src_mount])
        if dest:
            if subprocess.run(["mountpoint", "-q", self.dest_mount]).returncode == 0:
                print(f"{self.dest_mount} : Already Mounted")
                print()
            else:
                subprocess.run(["mount", "-t", "nfs", self.dest_export, self.dest_mount])

    # Unmount NFS filesystems
    def umount(self, src=True, dest=True):
        if src:
            if subprocess.run(["mountpoint", "-q", self.src_mount]).returncode == 0:
                subprocess.run(["umount", self.src_mount])
            else:
                print(f"Error: {self.src_mount} Not Mounted")
                print()
        if dest:
            if subprocess.run(["mountpoint", "-q", self.dest_mount]).returncode == 0:
                subprocess.run(["umount", self.dest_mount])
            else:
                print(f"Error: {self.dest_mount} Not Mounted")
                print()

    # Remove directory mount points
    def rmdir(self, src=True, dest=True):
        if src and os.path.isdir(self.src_mount):
            os.rmdir(self.src_mount)
        if dest and os.path.isdir(self.dest_mount):
            os.rmdir(self.dest_mount)

    # Rsync subprocess operation
    def rsync(self, extra_args=None):
        src_rc = subprocess.run(["mountpoint", "-q", self.src_mount]).returncode
        dest_rc = subprocess.run(["mountpoint", "-q", self.dest_mount]).returncode

        if src_rc == 0 and dest_rc == 0:
            if extra_args:
                rsync_args = ["rsync", "-havH"] + extra_args + [self.src_mount, self.dest_mount]
                r = subprocess.run(rsync_args)
            else:
                rsync_args = ["rsync", "-havH", self.src_mount, self.dest_mount]
                r = subprocess.run(rsync_args)
            return r
        else:
            if src_rc != 0:
                print(f"Error: {self.src_mount} Not Mounted")
            if dest_rc != 0:
                print(f"Error: {self.dest_mount} Not Mounted")
            print()
            
    # Pcopy subprocess operation
    def pcopy(self, extra_args=None):
        src_rc = subprocess.run(["mountpoint", "-q", self.src_mount]).returncode
        dest_rc = subprocess.run(["mountpoint", "-q", self.dest_mount]).returncode

        if src_rc == 0 and dest_rc == 0:
            if extra_args:
                pcopy_args = ["pcopy", "-pr"] + extra_args + [self.src_mount, self.dest_mount]
                subprocess.run(pcopy_args)
            else:
                pcopy_args = ["pcopy" "-pr", self.src_mount, self.dest_mount]
                subprocess.run(pcopy_args)
        else:
            if src_rc != 0:
                print(f"Error: {self.src_mount} Not Mounted")
            if dest_rc != 0:
                print(f"Error: {self.dest_mount} Not Mounted")
            print()