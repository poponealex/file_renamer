from pathlib import Path
from hashlib import sha256
from itertools import count

from typing import Iterable, Set, Generator


class FileSystem(set):

    def __init__(self, paths: Iterable[Path]):
        super().__init__(paths)
        if paths:  # when some initial paths are provided, the file system is considered as pure
            self.path_exists = lambda path: path in self
            self.siblings = lambda path: (sibling for sibling in self.children(path.parent))
        else:  # otherwise, the file system is considered as concrete
            self.path_exists = lambda path: path.exists()
            self.siblings = lambda path: path.parent.glob("*")

    def update_with_source_paths(self, source_paths: Iterable[Path]) -> None:
        """Check all paths exist in the file system and "close" it with their siblings.

        Args:
            source_paths (Iterable[Path]): the paths to be renamed.

        Raises:
            FileNotFoundError: a source path is absent from the file system.
        """
        result: Set[Path] = set()
        for source_path in source_paths:
            if not self.path_exists(source_path):
                raise FileNotFoundError(source_path)
            result.update(self.siblings(source_path))
        self.update(result) # should not change a pure file system

    def children(self, path: Path) -> Generator[Path, None, None]:

        for candidate in self:
            if candidate.match(f"{path}/*"):
                yield candidate

    def non_existing_sibling(self, path: Path) -> Path:
        """Create the path of a non-existing sibling of a given path.
        
        Args:
            path (Path): a source path which is the target of another renaming.

        Returns:
            Path: the path to be temporarily used for an intermediate renaming.
        """
        digest = sha256(path.stem.encode("utf8")).hexdigest()[:32]
        for suffix in count():
            new_path = path.with_stem(f"{digest}-{suffix}")
            if new_path not in self:
                return new_path
    
    def rename(self, path, new_path):
        """Rename a path into a new path, and renames recursively its descendants.
        
        The following preconditions are normally satisfied:

        1. `path` and `new_path` are siblings,
        2. `path` is in the file system,
        3. and `new_path` is not in the file system yet.

        Results:
            - `path` is replaced by `new_path` in the file system.
            - Any descendant of `path` is replaced by the appropriate `path`.
        
        Notes:
            - The renaming is virtual only. The ultimate goal is to produce a sequence of "safe"
                clauses for an ulterior actual renaming. Nevertheless, all the consquencees of a
                renaming (specifically, of a folder) are simulated to ensure testability.
            - In a virtual file system, renaming a node before its parent is not mandatory.
        """
        offset = len(str(path)) + 1
        for candidate in list(self):
            if candidate == path or str(candidate).startswith(f"{path}/"):
                self.remove(candidate)
                self.add(new_path / str(candidate)[offset:])
