# Author: Soumil Datta, Michael Davis

# Reciever

#import modules 
import hashlib
import json
import os
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="RemoteCabinet")

_token:    str              = ""
_cabinets: dict[str, Path] = {}

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
            rel  = str(p.relative_to(root))
            stat = p.stat()
            manifest[rel] = FileEntry(hash=_hash_file(p), mtime=stat.st_mtime, size=stat.st_size)
    return manifest

#converts the entire JSON-encoded to dictionary
def deserialize(data: dict[str, dict[str, str | float | int]]) -> Manifest:
    return {path: FileEntry.from_dict(entry) for path, entry in data.items()}

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
    AUTH_FAIL = "auth_fail"
    MANIFEST  = "manifest"
    SYNC_PLAN = "sync_plan"
    SYNC_DONE = "sync_done"
    ERROR     = "error"



 # pushes the files based on what is missing/changed. deletes everything else 
def plan_push(local: Manifest, remote: Manifest) -> tuple[list[str], list[str]]:
   
    to_push = [
        path for path, entry in local.items()
        if remote.get(path) is None or remote[path].hash != entry.hash
    ]
    to_delete = [path for path in remote if path not in local]
    return to_push, to_delete



def configure(token: str, cabinets: dict[str, Path]) -> None:
    global _token, _cabinets
    _token    = token
    _cabinets = {name: Path(p).resolve() for name, p in cabinets.items()}
    for p in _cabinets.values():
        p.mkdir(parents=True, exist_ok=True)


# WebSocket handler

@app.websocket("/sync/{cabinet}")
async def sync_ws(websocket: WebSocket, cabinet: str) -> None:
    await websocket.accept()

    root = _cabinets.get(cabinet)
    if root is None:
        await websocket.send_json({"type": Msg.ERROR, "message": f"unknown cabinet: {cabinet}"})
        await websocket.close()
        return

    try:
        # Auth will reject immediately if token is wrong
        msg = await websocket.receive_json()
        if msg.get("type") != Msg.AUTH or msg.get("token") != _token:
            await websocket.send_json({"type": Msg.AUTH_FAIL, "reason": "invalid token"})
            await websocket.close()
            return
        await websocket.send_json({"type": Msg.AUTH_OK})

        # Receives the client manifest 
        msg = await websocket.receive_json()
        if msg.get("type") != Msg.MANIFEST:
            await websocket.send_json({"type": Msg.ERROR, "message": "expected manifest"})
            await websocket.close()
            return

        client_manifest = deserialize(msg["files"])
        server_manifest = build(root)

        # Compute diff between what the server's current state has vs what it needs
        to_receive, to_delete = plan_push(client_manifest, server_manifest)
        await websocket.send_json({"type": Msg.SYNC_PLAN, "need": to_receive, "deleting": len(to_delete)})

        # Receive files as binary chunks until client is finished
        pending = set(to_receive)
        while pending:
            msg = await websocket.receive_json()
            if msg.get("type") == "file_header":
                await _receive_file(websocket, root, msg)
                pending.discard(msg["path"])
            elif msg.get("type") == Msg.SYNC_DONE:
                break

        # Delete files the client no longer has 
        for path in to_delete:
            dest = root / path
            if dest.exists():
                dest.unlink()
                _remove_empty_parents(dest, root)

        await websocket.send_json({"type": Msg.SYNC_DONE})
        print(f"Sync complete — pushed {len(to_receive)}, deleted {len(to_delete)}")

    except WebSocketDisconnect:
        pass


# File I/O Handler

async def _receive_file(websocket: WebSocket, root: Path, header: dict[str, str | float | int]) -> None:
    path         = header["path"]
    mtime        = header["mtime"]
    total_chunks = header["total_chunks"]

    chunks: list[bytes] = []
    for _ in range(total_chunks):
        chunks.append(await websocket.receive_bytes())

    dest = root / path
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file then rename atomically, while avoiding partial writes
    tmp = dest.with_suffix(dest.suffix + ".rc_partial")
    tmp.write_bytes(b"".join(chunks))
    tmp.rename(dest)
    os.utime(dest, (mtime, mtime))


def _remove_empty_parents(deleted: Path, root: Path) -> None:
    parent = deleted.parent
    while parent != root:
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
        parent = parent.parent


# Main function

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python -m RCServer <token> <cabinet_name> <cabinet_path> [port]")
        sys.exit(1)

    token        = sys.argv[1]
    cabinet_name = sys.argv[2]
    cabinet_path = Path(sys.argv[3]).resolve()
    port         = int(sys.argv[4]) if len(sys.argv) > 4 else 9000

    configure(token=token, cabinets={cabinet_name: cabinet_path})
    print(f"Serving cabinet '{cabinet_name}' → {cabinet_path} on :{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
