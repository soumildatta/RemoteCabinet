# Author: Soumil Datta, Michael Davis

# Sender

#import mudules
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from tqdm import tqdm

# manages connection for messages sending/receiving
import websockets
from websockets.asyncio.client import ClientConnection


CHUNK_SIZE = 1024 * 1024  # 1mb per chunk
IGNORE_PREFIXES = (".rc_", ".DS_Store")


# A filewatcher that monitors the state of all files within a directory and syncs when necessary  

@dataclass
# common file structure
class FileEntry:
    hash: str
    mtime: float
    size: int


    def to_dict(self) -> dict[str, str | float | int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, str | float | int]) -> "FileEntry":
        return cls(**d)

# init for manifest

Manifest = dict[str, FileEntry]

# traverses the entire directory under root dir, bypassing IGNORE_PREFIXES, and returns manifest,
# which is a snapshot of the directory within a point in time. 

def build(root: Path) -> Manifest:

    manifest: Manifest = {}
    for p in root.rglob("*"):
        if p.is_file() and not any(p.name.startswith(x) for x in IGNORE_PREFIXES):
            rel = str(p.relative_to(root))
            stat = p.stat()
            manifest[rel] = FileEntry(hash=_hash_file(p), mtime=stat.st_mtime, size=stat.st_size)
    return manifest

#converts the entire dictionary for JSON-encoded 
def serialize(manifest: Manifest) -> dict[str, dict[str, str | float | int]]:
    return {path: entry.to_dict() for path, entry in manifest.items()}

#computes a 16-byte BLAKE2b hash of a file's content in order avoid loading
# larger files into memory. 

def _hash_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=16)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# Protocol Handshake Messages
class Msg(str, Enum):
    AUTH      = "auth"
    AUTH_OK   = "auth_ok"
    MANIFEST  = "manifest"
    SYNC_DONE = "sync_done"


# pushes the files from local
def plan_push(local: Manifest, remote_data: dict[str, dict[str, str | float | int]]) -> tuple[list[str], list[str]]:
    remote = {path: FileEntry.from_dict(entry) for path, entry in remote_data.items()}
    to_push = [
        path for path, entry in local.items()
        if remote.get(path) is None or remote[path].hash != entry.hash
    ]
    to_delete = [path for path in remote if path not in local]
    return to_push, to_delete


# sends files in chunks over the websocket connection 
async def _send_file(ws: ClientConnection, path: str, local_dir: Path) -> None:
    src  = local_dir / path
    stat = src.stat()
    data = src.read_bytes()

    # is used for empty file scenarios (need to find alternative maybe)
    total_chunks = max(1, (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE)

# JSON header details 
    await ws.send(json.dumps({
        "type":         "file_header",
        "path":         path,
        "mtime":        stat.st_mtime,
        "size":         stat.st_size,
        "total_chunks": total_chunks,
    }))

# sends data in chunks to the server 
    for i in tqdm(range(total_chunks)):
        await ws.send(data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE])


# only activates when the watcher finds a change in the directory
async def _sync(server_url: str, token: str, cabinet: str, local_dir: Path) -> None:
    uri = f"{server_url}/sync/{cabinet}"
    local_dir.mkdir(parents=True, exist_ok=True)

    #connection starts 
    async with websockets.connect(uri) as ws:

        # Authentication 
        await ws.send(json.dumps({"type": Msg.AUTH, "token": token}))
        resp = json.loads(await ws.recv())
        if resp.get("type") != Msg.AUTH_OK:
            print(f"Auth failed: {resp.get('reason', 'unknown')}")
            return

        # Sends local manifest from client, where erver computes the diff
        local_manifest = build(local_dir)
        await ws.send(json.dumps({"type": Msg.MANIFEST, "files": serialize(local_manifest)}))

        # Receives sync plan from server
        plan          = json.loads(await ws.recv())
        need: list[str] = plan.get("need", [])
        deleting: int   = plan.get("deleting", 0)

        print(f"Sync plan: ↑ {len(need)} to push" + (f"  ✕ {deleting} to delete" if deleting else ""))

        # Pushes only the files the server needs, in binary chunks
        for path in need:
            print(f"  pushing {path}")
            await _send_file(ws, path, local_dir)

        await ws.send(json.dumps({"type": Msg.SYNC_DONE}))

        msg = json.loads(await ws.recv())
        if msg.get("type") == Msg.SYNC_DONE:
            print("Sync completed.")

# Loop to keep the client up-to-date with the server adter connection
async def _watch(server_url: str, token: str, cabinet: str, local_dir: Path, interval: float = 1.0) -> None:
    
    local_dir.mkdir(parents=True, exist_ok=True)
    
    last: Manifest | None = None

    print(f"Watching current local directory: {local_dir} (Ctrl+C to stop)")
    try:
        while True:
            current = build(local_dir)

            if current != last:
                if last is not None:
                    print("Changes detected — syncing...")

                await _sync(server_url, token, cabinet, local_dir)
                last = build(local_dir)

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("Watch stopped.")

# main function 
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python -m RCClient <ws://host:port> <token> <cabinet> <local_dir>")
        sys.exit(1)

    server_url = sys.argv[1]
    token      = sys.argv[2]
    cabinet    = sys.argv[3]
    local_dir  = Path(sys.argv[4]).resolve()

    asyncio.run(_watch(server_url, token, cabinet, local_dir))
