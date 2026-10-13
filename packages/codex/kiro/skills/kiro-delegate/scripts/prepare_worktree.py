#!/usr/bin/env python3
"""Prepare delegation support files without following destination symlinks.

Usage:
  prepare_worktree.py prepare --root DIR --worktree DIR --spec-name SLUG < prompt.txt
  prepare_worktree.py write-prompt --worktree DIR < retry-prompt.txt
  prepare_worktree.py new-run

Preparation refuses tracked support paths and existing support leaves before any
write. Retry text uses the separate write-prompt command. This protects support
file preparation, not the Kiro process or its applied-diff scope guard.
"""

import argparse
import contextlib
import os
import re
import stat
import subprocess
import sys
import tempfile

try:
    import fcntl
except ImportError:
    fcntl = None


class Refusal(Exception):
    """An unsafe or conflicting support-file destination."""


def _identity(info):
    return info.st_dev, info.st_ino


class SafeTree:
    """Hold no-follow directory descriptors and recheck their parent links."""

    def __init__(self, root):
        if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
                or fcntl is None):
            raise Refusal("this platform lacks required no-follow filesystem operations")
        self.root = os.path.abspath(root)
        self.fds = {}
        self.links = []
        fd = os.open(os.path.sep, os.O_RDONLY | os.O_DIRECTORY)
        self.fds["/"] = fd
        try:
            for part in self.root.split(os.path.sep):
                if not part:
                    continue
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=fd)
                self.links.append((fd, part, child))
                self.fds[f"/{len(self.links)}"] = child
                fd = child
            self.fds[""] = fd
        except OSError:
            self.close()
            raise Refusal(f"root contains a symlink or invalid directory: {self.root}")

    def close(self):
        for fd in set(self.fds.values()):
            os.close(fd)
        self.fds.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def verify(self):
        for parent, name, child in self.links:
            try:
                info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except OSError as exc:
                raise Refusal(f"directory changed during preparation: {name}") from exc
            if not stat.S_ISDIR(info.st_mode) or _identity(info) != _identity(os.fstat(child)):
                raise Refusal(f"directory changed during preparation: {name}")

    def directory(self, relative, create=False):
        if relative in self.fds:
            return self.fds[relative]
        parent, _, name = relative.rpartition("/")
        parent_fd = self.directory(parent, create=create)
        if parent_fd is None:
            return None
        try:
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                         dir_fd=parent_fd)
        except FileNotFoundError:
            if not create:
                return None
            self.verify()
            try:
                os.mkdir(name, mode=0o700, dir_fd=parent_fd)
            except FileExistsError:
                # A concurrent creator is still checked with O_NOFOLLOW below.
                pass
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                         dir_fd=parent_fd)
        except OSError as exc:
            raise Refusal(f"symlink or invalid support directory: {relative}") from exc
        self.fds[relative] = fd
        self.links.append((parent_fd, name, fd))
        self.verify()
        return fd

    def leaf(self, relative):
        parent, _, name = relative.rpartition("/")
        fd = self.directory(parent)
        if fd is None:
            return None
        try:
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise Refusal(f"symlink, hardlink or invalid support file: {relative}")
        return info

    def read(self, relative):
        expected = self.leaf(relative)
        if expected is None:
            raise Refusal(f"required support source is missing: {relative}")
        parent, _, name = relative.rpartition("/")
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=self.directory(parent))
        with os.fdopen(fd, "rb") as stream:
            if _identity(os.fstat(stream.fileno())) != _identity(expected):
                raise Refusal(f"support source changed during preparation: {relative}")
            self.verify()
            return stream.read()

    def create(self, relative, data):
        parent, _, name = relative.rpartition("/")
        parent_fd = self.directory(parent, create=True)
        self.verify()
        # O_EXCL refuses a newly planted symlink or any other leaf collision.
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent_fd)
        with os.fdopen(fd, "wb") as stream:
            self.verify()
            self.verify_leaf(relative, stream.fileno())
            stream.write(data)
            stream.flush()
            self.verify()
            self.verify_leaf(relative, stream.fileno())
            return _identity(os.fstat(stream.fileno()))

    def verify_leaf(self, relative, fd):
        parent, _, name = relative.rpartition("/")
        info = os.stat(name, dir_fd=self.directory(parent), follow_symlinks=False)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or _identity(info) != _identity(os.fstat(fd))):
            raise Refusal(f"support leaf changed during preparation: {relative}")


def _git(directory, *args):
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_PAGER": "cat", "GIT_OPTIONAL_LOCKS": "0"}
    result = subprocess.run(
        ["git", "-C", directory, "--literal-pathspecs", "-c", "core.fsmonitor=",
         "-c", f"core.hooksPath={os.devnull}", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False,
    )
    if result.returncode:
        raise Refusal("git support-file validation failed")
    return result.stdout


def _tracked_collisions(worktree, spec_name):
    prefixes = (".kiro/agents/kiro-implementer.json",
                f".kiro/specs/{spec_name}", ".kiro/task-prompt.md")
    for encoded in _git(worktree, "ls-files", "-z", "--", ".kiro").split(b"\0"):
        if not encoded:
            continue
        path = os.fsdecode(encoded)
        if any(path == p or path.startswith(p + "/") or p.startswith(path + "/")
               for p in prefixes):
            raise Refusal(f"tracked support path: {path}; use a fresh untracked convention")


def _exclude_path(worktree):
    # --path-format=absolute resolves a leaf symlink on current Git, hiding the
    # very path we must inspect. Anchor the uncanonicalized git-path ourselves.
    path = os.fsdecode(_git(worktree, "rev-parse", "--git-path", "info/exclude")).strip()
    return os.path.abspath(path if os.path.isabs(path) else os.path.join(worktree, path))


def _append_excludes(tree, expected, patterns):
    tree.verify()
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    if expected is None:
        flags |= os.O_CREAT | os.O_EXCL
    fd = os.open("exclude", flags, 0o600, dir_fd=tree.directory(""))
    with os.fdopen(fd, "r+b") as stream:
        actual = os.fstat(stream.fileno())
        if (not stat.S_ISREG(actual.st_mode) or actual.st_nlink != 1
                or (expected is not None and _identity(actual) != _identity(expected))):
            raise Refusal("git exclude file changed during preparation")
        # Linked worktrees share excludes; serialize concurrent run updates.
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        tree.verify()
        tree.verify_leaf("exclude", stream.fileno())
        previous = stream.read()
        existing = previous.splitlines()
        added = [os.fsencode(p) for p in patterns if os.fsencode(p) not in existing]
        if added:
            stream.seek(0, os.SEEK_END)
            stream.write((b"\n" if previous and not previous.endswith(b"\n") else b"")
                         + b"\n".join(added) + b"\n")
        stream.flush()
        tree.verify()
        tree.verify_leaf("exclude", stream.fileno())
        return _identity(os.fstat(stream.fileno()))


def prepare(root, worktree, spec_name, prompt):
    if re.fullmatch(r"[A-Za-z0-9_-]+", spec_name) is None:
        raise Refusal("spec-name must match [A-Za-z0-9_-]+")
    root, worktree = os.path.abspath(root), os.path.abspath(worktree)
    if root == worktree:
        raise Refusal("delegation requires a separate worktree")
    # Every source read, destination check, tracked check and exclude check precedes
    # all directory/file creation. Later races are handled by no-follow opens.
    with contextlib.ExitStack() as stack:
        source = stack.enter_context(SafeTree(root))
        destination = stack.enter_context(SafeTree(worktree))
        for path in (root, worktree):
            toplevel = os.fsdecode(_git(path, "rev-parse", "--show-toplevel")).strip()
            if os.path.abspath(toplevel) != path:
                raise Refusal("root and worktree must each name their checkout root")
        spec_dir = f".kiro/specs/{spec_name}"
        source_fd = source.directory(spec_dir)
        if source_fd is None:
            raise Refusal("spec source directory is missing")
        spec_files = sorted(name for name in os.listdir(source_fd) if name.endswith(".md"))
        if not {"requirements.md", "design.md", "tasks.md"}.issubset(spec_files):
            raise Refusal("spec requires requirements.md, design.md and tasks.md")
        contents = {".kiro/agents/kiro-implementer.json":
                    source.read(".kiro/agents/kiro-implementer.json")}
        contents.update({f"{spec_dir}/{name}": source.read(f"{spec_dir}/{name}")
                         for name in spec_files})
        contents[".kiro/task-prompt.md"] = prompt
        _tracked_collisions(worktree, spec_name)
        for relative in contents:
            if destination.leaf(relative) is not None:
                raise Refusal(f"support destination already exists: {relative}")
        exclude_path = _exclude_path(worktree)
        excludes = stack.enter_context(SafeTree(os.path.dirname(exclude_path)))
        exclude_info = excludes.leaf("exclude")
        source.verify()
        destination.verify()
        excludes.verify()
        # Re-read the index before mutation, so a collision added during preflight
        # is also refused without modifying support files.
        _tracked_collisions(worktree, spec_name)
        created = {relative: destination.create(relative, data)
                   for relative, data in contents.items()}
        patterns = ("/.kiro/agents/kiro-implementer.json",
                    f"/.kiro/specs/{spec_name}/", "/.kiro/task-prompt.md")
        exclude_identity = _append_excludes(excludes, exclude_info, patterns)
        # Exclude updates are a separate phase. Recheck final support state before
        # reporting success, including any directory/leaf replacement in that phase.
        source.verify()
        excludes.verify()
        destination.verify()
        final_exclude = excludes.leaf("exclude")
        if final_exclude is None or _identity(final_exclude) != exclude_identity:
            raise Refusal("git exclude leaf changed before preparation completed")
        final_patterns = excludes.read("exclude").splitlines()
        if not all(os.fsencode(pattern) in final_patterns for pattern in patterns):
            raise Refusal("required git exclude patterns changed before preparation completed")
        for relative, identity in created.items():
            info = destination.leaf(relative)
            if info is None or _identity(info) != identity:
                raise Refusal(f"support leaf changed before preparation completed: {relative}")
            if destination.read(relative) != contents[relative]:
                raise Refusal(f"support contents changed before preparation completed: {relative}")
        destination.verify()
        excludes.verify()


def write_prompt(worktree, prompt):
    relative = ".kiro/task-prompt.md"
    with SafeTree(worktree) as tree:
        expected = tree.leaf(relative)
        if expected is None:
            raise Refusal("retry prompt is missing; prepare the worktree first")
        _tracked_collisions(worktree, "__retry_prompt_check__")
        fd = os.open("task-prompt.md", os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=tree.directory(".kiro"))
        with os.fdopen(fd, "wb") as stream:
            actual = os.fstat(stream.fileno())
            if _identity(actual) != _identity(expected) or actual.st_nlink != 1:
                raise Refusal("retry prompt changed during preparation")
            tree.verify()
            tree.verify_leaf(relative, stream.fileno())
            # Opening above does not truncate; validate the opened inode first.
            os.ftruncate(stream.fileno(), 0)
            stream.write(prompt)
            stream.flush()
            tree.verify()
            tree.verify_leaf(relative, stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preparing = sub.add_parser("prepare")
    preparing.add_argument("--root", required=True)
    preparing.add_argument("--worktree", required=True)
    preparing.add_argument("--spec-name", required=True)
    retry = sub.add_parser("write-prompt")
    retry.add_argument("--worktree", required=True)
    sub.add_parser("new-run")
    args = parser.parse_args()
    try:
        if args.command == "new-run":
            # Do not use a consumer-controlled TMPDIR that could be in a worktree.
            print(tempfile.mkdtemp(prefix="kiro-delegate-", dir="/tmp"))
        elif args.command == "prepare":
            prepare(args.root, args.worktree, args.spec_name, sys.stdin.buffer.read())
        else:
            write_prompt(args.worktree, sys.stdin.buffer.read())
    except (Refusal, OSError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
