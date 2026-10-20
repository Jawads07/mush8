"""Private inputs and structural IPA verification for the macOS cloud build."""

import contextlib
import io
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

FILES = ("prod.keys", "base.nsp", "upd4-0-1.nsp")


def download():
    url = os.environ["MUSH8_INPUTS_URL"].strip()
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("The input archive must use an HTTPS URL.")
    # Store the URL only in an Actions secret, never in the workflow or logs.
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "inputs.zip"
        try:
            if parsed.hostname == "drive.google.com":
                import gdown

                # Drive serves a confirmation page for large files. Keep both the
                # share URL and any resolved download URLs out of public CI logs.
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    gdown.download(url=url, output=str(archive), quiet=True, use_cookies=False)
            else:
                with urllib.request.urlopen(url, timeout=120) as response:
                    if urllib.parse.urlsplit(response.url).scheme != "https":
                        raise ValueError("The download redirected away from HTTPS.")
                    with archive.open("wb") as out:
                        shutil.copyfileobj(response, out)
        except Exception:
            raise RuntimeError("Could not download the input ZIP. Check the link, download permission, quota, and expiry.") from None

        with zipfile.ZipFile(archive) as package:
            for name in FILES:
                matches = [item for item in package.infolist() if item.filename == name]
                if len(matches) != 1:
                    raise ValueError(f"The ZIP must contain exactly one {name} at its root.")
                item = matches[0]
                if item.is_dir() or stat.S_ISLNK(item.external_attr >> 16) or item.file_size == 0:
                    raise ValueError(f"{name} must be a nonempty regular file.")
                if item.file_size > 16 * 1024**3:
                    raise ValueError(f"{name} exceeds the 16 GiB input limit.")
            needed = sum(package.getinfo(name).file_size for name in FILES)
            if shutil.disk_usage(".").free < needed + 8 * 1024**3:
                raise RuntimeError("Not enough disk space for the inputs plus 8 GiB of build space.")
            # Copy only the three exact filenames; never extract arbitrary archive paths.
            for name in FILES:
                with package.open(name) as source, open(name, "wb") as target:
                    shutil.copyfileobj(source, target)
                os.chmod(name, 0o600)
    print("The three private build inputs are ready.")


def verify():
    with zipfile.ZipFile("build/Mush8.ipa") as package:
        names = set(package.namelist())
        prefix = "Payload/Mush8.app/"
        for name in ("Info.plist", "nxhost", "modules/main.npdm", "shaders/index.tsv", "shaders/guest.tsv"):
            if prefix + name not in names or package.getinfo(prefix + name).file_size == 0:
                raise ValueError(f"IPA is missing a nonempty {name}.")
        if not any(name.startswith(prefix + "shaders/") and name.endswith(".metallib") for name in names):
            raise ValueError("IPA contains no compiled Metal shader libraries.")
        if any(Path(name).name in FILES for name in names):
            raise ValueError("IPA unexpectedly contains private input files.")
    print("IPA structure verified; physical-device testing is still needed.")


if __name__ == "__main__":
    if sys.argv[1:] == ["download"]:
        download()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("Usage: python3 tools/cloud-ipa.py download|verify")
