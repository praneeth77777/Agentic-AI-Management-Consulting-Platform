from __future__ import annotations
import argparse, shutil, zipfile
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description="Extract only approved hackathon sources into ignored data/raw.")
    p.add_argument("hackathon_zip")
    p.add_argument("--out", default="data/raw")
    args = p.parse_args()
    src, out = Path(args.hackathon_zip), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    temp = out / "_course_extract"
    if temp.exists(): shutil.rmtree(temp)
    with zipfile.ZipFile(src) as z: z.extractall(temp)
    base = temp / "Hackathon"
    (out / "technology").mkdir(exist_ok=True)
    for name in ["DataSource-Cisco.txt", "Google GCP.txt"]:
        if (base/name).exists(): shutil.copy2(base/name, out/"technology"/name)
    seczip = base / "UnitedStatesSecuritiesandExchangeCommission(SEC).zip"
    if seczip.exists():
        secout = out / "sec"; secout.mkdir(exist_ok=True)
        with zipfile.ZipFile(seczip) as z: z.extractall(secout)
    shutil.rmtree(temp)
    print(f"Prepared local course data under {out}. These files are git-ignored; do not commit them.")

if __name__ == "__main__": main()
