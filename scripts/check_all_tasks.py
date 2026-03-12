#!/usr/bin/env python3
"""
Unified autograder for 5 tasks (GitHub Classroom / Actions friendly).
- Prints detailed diagnostics
- Exits non-zero on failure, zero on success
- Prints "RESULT: PASS" only when everything passes
"""
import sys
import re
from pathlib import Path
from typing import List, Optional

# --------------------- Utilities ---------------------

def eprint(msg: str):
    print(f"::error::{msg}")

def wprint(msg: str):
    print(f"::warning::{msg}")

def info(msg: str):
    print(msg)

def read_text(path: Path) -> str:
    if not path.exists():
        eprint(f"Missing required file: {path}")
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8', errors='replace')

def word_count(text: str) -> int:
    tokens = re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?", text)
    return len(tokens)

def detect_headings(md: str, level: Optional[int] = None) -> List[str]:
    if level is None:
        pattern = r"(?m)^(#+\s.+?)\s*$"
    else:
        hashes = '#' * level
        pattern = rf"(?m)^({re.escape(hashes)}\s.+?)\s*$"
    return re.findall(pattern, md)

def extract_section_body(md: str, heading_text: str) -> Optional[str]:
    """Extract text under the given heading (exact literal) up to the next heading of same or higher level, or EOF."""
    m = re.match(r"^(#+)\s", heading_text)
    if not m:
        return None
    level = len(m.group(1))

    start_match = re.search(rf"(?m)^{re.escape(heading_text)}\s*\n", md)
    if not start_match:
        return None
    start = start_match.end()

    # Next heading of same or higher level
    next_pat = rf"(?m)^#{{1,{level}}}\s"
    next_match = re.search(next_pat, md[start:])
    end = start + (next_match.start() if next_match else len(md))

    body = md[start:end].strip()
    # Remove horizontal rules like --- or *** lines
    body = re.sub(r"(?m)^\s*[-*_]{3,}\s*$", "", body).strip()
    return body

# --------------------- Task 1 ---------------------

def check_task1(errors: List[str]):
    path = Path('01_hardware_vs_software.md')
    try:
        md = read_text(path)
    except FileNotFoundError:
        errors.append("Task 1: Missing file 01_hardware_vs_software.md")
        return

    H1 = "# Part 1 – Hardware vs Software"
    sections = [
        "## Explain Hardware",
        "## Explain Software",
        "## How Do Hardware and Software Interact?",
    ]

    if not re.search(rf"(?m)^{re.escape(H1)}\s*$", md):
        errors.append("Task 1: Missing exact H1 '# Part 1 – Hardware vs Software'")

    for h in sections:
        if not re.search(rf"(?m)^{re.escape(h)}\s*$", md):
            detected = detect_headings(md, level=2)
            errors.append(f"Task 1: Missing section '{h}'. Found H2: {detected}")
            continue
        body = extract_section_body(md, h)
        if body is None:
            errors.append(f"Task 1: Could not extract body for '{h}'")
            continue
        wc = word_count(body)
        if wc < 50:
            errors.append(f"Task 1: Section '{h}' has {wc} words; expected ≥ 50")
        else:
            info(f"Task 1: {h} OK ({wc} words)")

# --------------------- Task 2 ---------------------

def check_task2(errors: List[str]):
    path = Path('02_computer_disassembly.md')
    try:
        md = read_text(path)
    except FileNotFoundError:
        errors.append("Task 2: Missing file 02_computer_disassembly.md")
        return

    sections = [
        "## Before Opening the Computer",
        "## Internal Layout",
    ]
    for h in sections:
        if not re.search(rf"(?m)^{re.escape(h)}\s*$", md):
            errors.append(f"Task 2: Missing section '{h}'")
            continue
        body = extract_section_body(md, h)
        if body is None:
            errors.append(f"Task 2: Could not extract body for '{h}'")
            continue
        wc = word_count(body)
        if wc < 20:  # adjustable threshold
            errors.append(f"Task 2: Section '{h}' has {wc} words; expected ≥ 20")
        else:
            info(f"Task 2: {h} OK ({wc} words)")

    required_images = [
        Path('images/system/computer-before.jpg'),
        Path('images/system/computer-opened.jpg'),
    ]
    for img in required_images:
        if not img.exists():
            errors.append(f"Task 2: Missing required image '{img.as_posix()}'")
        else:
            info(f"Task 2: Found image {img.as_posix()}")

# --------------------- Task 3 ---------------------

def _table_row(md: str, comp: str, two_cols: bool=False):
    if two_cols:
        return re.search(rf"(?mi)^\|\s*{re.escape(comp)}\s*\|\s*(.*?)\s*\|\s*$", md)
    else:
        return re.search(rf"(?mi)^\|\s*{re.escape(comp)}\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", md)

def check_task3(errors: List[str]):
    path = Path('03_component_investigation.md')
    try:
        md = read_text(path)
    except FileNotFoundError:
        errors.append("Task 3: Missing file 03_component_investigation.md")
        return

    if not re.search(r"(?mi)^\|\s*Component\s*\|\s*Function\s*\|\s*Key\s*Specification\s*\|\s*$", md):
        errors.append("Task 3: Missing table header '| Component | Function | Key Specification |'")

    required = ["CPU", "RAM", "Storage", "Motherboard", "Power Supply", "Cooling"]
    for comp in required:
        m = _table_row(md, comp, two_cols=False)
        if not m:
            errors.append(f"Task 3: Missing row for component '{comp}'")
            continue
        func, spec = m.group(1).strip(), m.group(2).strip()
        if not func:
            errors.append(f"Task 3: Component '{comp}' has empty Function cell")
        if not spec:
            errors.append(f"Task 3: Component '{comp}' has empty Key Specification cell")
        if func and spec:
            info(f"Task 3: Row '{comp}' OK")

    # Advisory check for photos
    img_dir = Path('images/components')
    if not img_dir.exists():
        wprint("Task 3: Expected folder 'images/components/' not found (advisory)")
    else:
        imgs = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.jpeg')) + list(img_dir.glob('*.png'))
        if len(imgs) == 0:
            wprint("Task 3: No images found in 'images/components/' (advisory)")
        else:
            info(f"Task 3: Found {len(imgs)} image(s) in images/components/")

# --------------------- Task 4 ---------------------

def check_task4(errors: List[str]):
    path = Path('04_raspberry_pi_identification.md')
    try:
        md = read_text(path)
    except FileNotFoundError:
        errors.append("Task 4: Missing file 04_raspberry_pi_identification.md")
        return

    # Required images
    for img in [Path('images/raspberry-pi/pi-board.jpg'), Path('images/raspberry-pi/labelled-pi-board.jpg')]:
        if not img.exists():
            errors.append(f"Task 4: Missing required image '{img.as_posix()}'")
        else:
            info(f"Task 4: Found image {img.as_posix()}")

    # Table header and rows
    if not re.search(r"(?mi)^\|\s*Component\s*\|\s*Function\s*\|\s*$", md):
        errors.append("Task 4: Missing table header '| Component | Function |'")
    components = ["SoC", "GPIO", "USB", "HDMI", "Power", "microSD", "Network", "Wireless"]
    for comp in components:
        m = _table_row(md, comp, two_cols=True)
        if not m:
            errors.append(f"Task 4: Missing row for component '{comp}'")
            continue
        func = m.group(1).strip()
        if not func:
            errors.append(f"Task 4: Component '{comp}' has empty Function cell")
        else:
            info(f"Task 4: Row '{comp}' OK")

    # Reflection ≥ 100 words
    refl_heading = "## Reflection"
    if not re.search(rf"(?m)^{re.escape(refl_heading)}\s*$", md):
        errors.append("Task 4: Missing '## Reflection' section")
    else:
        body = extract_section_body(md, refl_heading)
        if body is None:
            errors.append("Task 4: Could not extract Reflection body")
        else:
            wc = word_count(body)
            if wc < 100:
                errors.append(f"Task 4: Reflection has {wc} words; expected ≥ 100")
            else:
                info(f"Task 4: Reflection OK ({wc} words)")

# --------------------- Task 5 ---------------------

def check_task5(errors: List[str]):
    path = Path('05_reflection.md')
    try:
        md = read_text(path)
    except FileNotFoundError:
        errors.append("Task 5: Missing file 05_reflection.md")
        return

    h1 = "# Part 5 – Final Reflection"
    if not re.search(rf"(?m)^{re.escape(h1)}\s*$", md):
        errors.append("Task 5: Missing exact H1 '# Part 5 – Final Reflection'")
        return

    body = extract_section_body(md, h1)
    if body is None:
        errors.append("Task 5: Could not extract reflection body")
        return

    wc = word_count(body)
    if wc < 200 or wc > 300:
        errors.append(f"Task 5: Final reflection has {wc} words; expected 200–300")
    else:
        info(f"Task 5: Final reflection OK ({wc} words)")

# --------------------- Main ---------------------

def main():
    errors: List[str] = []
    info("=== Running autograder checks ===")
    check_task1(errors)
    check_task2(errors)
    check_task3(errors)
    check_task4(errors)
    check_task5(errors)

    if errors:
        for msg in errors:
            eprint(msg)
        print("RESULT: FAIL")
        sys.exit(1)
    else:
        print("All checks passed.")
        print("RESULT: PASS")
        sys.exit(0)

if __name__ == '__main__':
    main()
