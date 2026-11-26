#!/usr/bin/env python3
"""Validate a competition submission archive against packaging rules.

Checks the parts of the official submission spec that can be verified from the
archive itself: filename pattern, size limit, zip integrity, encrypted members,
required files, extraction, text encoding, garbled member names.

The upload-count limit and "does it actually run after unzip" cannot be checked
here and must stay on the manual checklist.

Exit codes: 0 all checks passed, 1 at least one failure, 2 archive unreadable.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import zipfile

TEXT_SUFFIXES = {
    ".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".html",
    ".css", ".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".c", ".h", ".cpp",
    ".hpp", ".go", ".rs", ".sql", ".ini", ".cfg", ".conf", ".tex",
}

MOJIBAKE_MARKERS = ("锟斤拷", "ï¿½", "â€™", "â€œ", "��")

MAX_TEXT_FILES = 200
MAX_TEXT_BYTES = 5 * 1024 * 1024


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, msg: str) -> None:
        self.passed += 1
        print(f"[PASS] {msg}")

    def fail(self, msg: str) -> None:
        self.failed += 1
        print(f"[FAIL] {msg}")

    def info(self, msg: str) -> None:
        print(f"[INFO] {msg}")


def member_matches(required: str, names: list[str]) -> bool:
    """A required file may be given as a full path or just a file name."""
    if required in names:
        return True
    for name in names:
        base = os.path.basename(name)
        if base == required or name.endswith("/" + required):
            return True
    return False


def check_name(report: Report, archive: str, pattern: str) -> None:
    name = os.path.basename(archive)
    if re.match(pattern, name):
        report.ok(f"filename matches {pattern}: {name}")
    else:
        report.fail(f"filename '{name}' does not match {pattern}")


def check_size(report: Report, archive: str, max_mb: float) -> None:
    size_mb = os.path.getsize(archive) / (1024 * 1024)
    if size_mb < max_mb:
        report.ok(f"size {size_mb:.2f} MB is under the {max_mb:g} MB limit")
    else:
        report.fail(f"size {size_mb:.2f} MB reaches or exceeds the {max_mb:g} MB limit")


def check_garbled_names(report: Report, names: list[str]) -> None:
    hits = []
    for name in names:
        if any(marker in name for marker in MOJIBAKE_MARKERS):
            hits.append(name)
    if hits:
        preview = ", ".join(hits[:5])
        report.fail(f"{len(hits)} member name(s) look garbled: {preview}")
    else:
        report.ok("no garbled member names")


def check_encoding(report: Report, zf: zipfile.ZipFile, names: list[str]) -> None:
    text_files = [
        n for n in names
        if not n.endswith("/") and os.path.splitext(n)[1].lower() in TEXT_SUFFIXES
    ]
    if not text_files:
        report.info("no text files to check for UTF-8")
        return

    bad = []
    skipped = 0
    for name in text_files[:MAX_TEXT_FILES]:
        try:
            data = zf.read(name)
        except (RuntimeError, zipfile.BadZipFile, OSError):
            skipped += 1
            continue
        if len(data) > MAX_TEXT_BYTES:
            skipped += 1
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            bad.append(name)

    if len(text_files) > MAX_TEXT_FILES:
        skipped += len(text_files) - MAX_TEXT_FILES

    if bad:
        report.fail(f"{len(bad)} text file(s) are not valid UTF-8: {', '.join(bad[:5])}")
    else:
        report.ok(f"all {len(text_files) - skipped} checked text file(s) decode as UTF-8")
    if skipped:
        report.info(f"{skipped} file(s) skipped (too large or unreadable)")


def check_extract(report: Report, zf: zipfile.ZipFile) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            zf.extractall(tmp)
        except Exception as exc:  # noqa: BLE001 - report any extraction failure
            report.fail(f"extraction failed: {exc}")
            return
        extracted = []
        for root, _dirs, files in os.walk(tmp):
            extracted.extend(os.path.join(root, f) for f in files)
        if not extracted:
            report.fail("extraction produced no files")
        else:
            report.ok(f"extracted {len(extracted)} file(s) cleanly")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a competition submission archive."
    )
    parser.add_argument("archive", help="path to the submission .zip")
    parser.add_argument(
        "--naming",
        default=r"^.+-.+\.zip$",
        help="regex the file name must match (default: track-account.zip)",
    )
    parser.add_argument(
        "--max-size-mb", type=float, default=500.0,
        help="size limit in MB, exclusive (default: 500)",
    )
    parser.add_argument(
        "--require", action="append", default=[], metavar="NAME",
        help="required member file name; repeatable",
    )
    parser.add_argument(
        "--skip-extract", action="store_true",
        help="skip the unzip test (faster on very large archives)",
    )
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass

    if not os.path.isfile(args.archive):
        print(f"ERROR: archive not found: {args.archive}")
        return 2

    report = Report()
    check_name(report, args.archive, args.naming)
    check_size(report, args.archive, args.max_size_mb)

    try:
        zf = zipfile.ZipFile(args.archive)
    except zipfile.BadZipFile as exc:
        print(f"ERROR: not a readable zip archive: {exc}")
        return 2

    with zf:
        corrupted = zf.testzip()
        if corrupted is None:
            report.ok("zip integrity check passed")
        else:
            report.fail(f"corrupted member: {corrupted}")

        infos = zf.infolist()
        encrypted = [i.filename for i in infos if i.flag_bits & 0x1]
        if encrypted:
            report.fail(f"{len(encrypted)} encrypted member(s): {', '.join(encrypted[:5])}")
        else:
            report.ok("no encrypted members")

        names = zf.namelist()
        if not names:
            report.fail("archive contains no members")
        else:
            report.info(f"archive holds {len(names)} member(s)")

        for required in args.require:
            if member_matches(required, names):
                report.ok(f"required member present: {required}")
            else:
                report.fail(f"required member missing: {required}")

        tops = sorted({n.split("/")[0] for n in names if n and not n.endswith("/")})
        if tops:
            report.info(f"top level entries: {', '.join(tops[:20])}")

        check_garbled_names(report, names)
        check_encoding(report, zf, names)
        if args.skip_extract:
            report.info("extraction test skipped by request")
        else:
            check_extract(report, zf)

    print()
    print("MANUAL CHECKS (not verifiable from the archive):")
    print("- upload count within the allowed number of attempts")
    print("- the archive still runs after extraction on a clean machine")
    print("- required declarations are signed, not just present")

    print()
    print(f"SUMMARY: {report.passed} passed, {report.failed} failed")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
