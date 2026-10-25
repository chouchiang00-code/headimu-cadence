"""Extract only the files the analysis needs from the Voisard archive (meta, processed, raw HE/LB/LF).
Usage: python extract_needed.py <dataset.zip> <output folder>
Already-extracted files with the right size are skipped, so the script can be re-run safely."""
import sys
import zipfile
from pathlib import Path

KEEP = ("_meta.json", "_processed_data.txt", "_processed.txt", "_raw_data_HE.txt", "_raw_data_LB.txt", "_raw_data_LF.txt")


def main(zpath, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        members = [m for m in z.infolist() if not m.is_dir() and m.filename.endswith(KEEP)]
        n_meta = sum(m.filename.endswith("_meta.json") for m in members)
        print(f"archive: {len(members)} files to extract, {n_meta} trials")
        done = 0
        for k, m in enumerate(members):
            dest = out / m.filename
            if dest.exists() and dest.stat().st_size == m.file_size:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(m) as src, open(dest, "wb") as dst:
                while True:
                    b = src.read(1 << 20)
                    if not b:
                        break
                    dst.write(b)
            done += 1
            if done % 500 == 0:
                print(f"  extracted {done} files ({k + 1}/{len(members)})", flush=True)
    print(f"extraction finished: {done} new files -> {out.resolve()}")


# Command-line usage; valid analysis invocations are unchanged.
if __name__ == "__main__":
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print('Usage: python extract_needed.py DATASET_ZIP OUTPUT_DIR')
        raise SystemExit(0)
    if len(sys.argv) < 3:
        print('Usage: python extract_needed.py DATASET_ZIP OUTPUT_DIR', file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
