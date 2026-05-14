import os
import re

SLIDE_SEP = re.compile(r'(?m)^--$')
COMMENT_RE = re.compile(r'<!--(.*?)-->', re.DOTALL)
TIMING_RE = re.compile(r'\[([^\]]*?\d+[^\]]*?;[^\]]*?\d+[^\]]*?)\]')


def parse_time(t_str: str) -> tuple[int, int]:
    """Parses various time formats like '1m 15s', '1m15s', '45s', '20:45', 'T: 20:45'"""
    t_str = t_str.strip().replace("T:", "").strip()

    m = re.match(r'^(\d+)[:.](\d+)$', t_str)
    if m:
        return int(m.group(1)), int(m.group(2))

    minutes = 0
    seconds = 0
    m_match = re.search(r'(\d+)\s*m', t_str)
    s_match = re.search(r'(\d+)\s*s', t_str)

    if m_match:
        minutes = int(m_match.group(1))
    if s_match:
        seconds = int(s_match.group(1))

    if not m_match and not s_match:
        nums = re.findall(r'\d+', t_str)
        if len(nums) == 1:
            seconds = int(nums[0])
        elif len(nums) == 2:
            minutes, seconds = int(nums[0]), int(nums[1])

    if seconds >= 60:
        minutes += seconds // 60
        seconds = seconds % 60

    return minutes, seconds


def format_segment_1(minutes: int, seconds: int) -> str:
    if minutes == 0:
        return f"{seconds}s"
    if seconds == 0:
        return f"{minutes}m"
    return f"{minutes}m {seconds:02d}s"


def format_segment_2(minutes: int, seconds: int) -> str:
    if minutes == 0:
        return f"{seconds}s"
    return f"{minutes}m {seconds:02d}s"


def is_slide_hidden(slide_text: str) -> bool:
    for m in COMMENT_RE.finditer(slide_text):
        content = m.group(1).lstrip()
        if not content.startswith('.slide:'):
            continue
        attrs = content[len('.slide:'):]
        if re.search(r'data-visibility\s*=\s*"hidden"', attrs):
            return True
    return False


def get_slide_duration(slide_text: str) -> tuple[int, int] | None:
    m = TIMING_RE.search(slide_text)
    if m:
        content = m.group(1)
        if ';' in content:
            parts = content.split(';')
            if len(parts) == 2:
                return parse_time(parts[0])
    return None


def update_slide_t(slide_text: str, cum_minutes: int, cum_seconds: int) -> str:
    def replace(m: re.Match) -> str:
        content = m.group(1)
        if ';' not in content:
            return m.group(0)
        parts = content.split(';')
        if len(parts) != 2:
            return m.group(0)
        m1, s1 = parse_time(parts[0])
        return f"[{format_segment_1(m1, s1)}; T: {format_segment_2(cum_minutes, cum_seconds)}]"

    return TIMING_RE.sub(replace, slide_text)


posts_dir = '_posts'
files = sorted(
    os.path.join(root, f)
    for root, _, fs in os.walk(posts_dir)
    for f in fs
    if f.endswith('.md')
)

cumulative_seconds = 0

for file_path in files:
    with open(file_path, encoding='utf-8') as fh:
        content = fh.read()

    slides = SLIDE_SEP.split(content)
    new_slides = []

    for slide in slides:
        if is_slide_hidden(slide):
            new_slides.append(slide)
            continue

        duration = get_slide_duration(slide)
        if duration is not None:
            cumulative_seconds += duration[0] * 60 + duration[1]

        cum_m, cum_s = divmod(cumulative_seconds, 60)
        new_slides.append(update_slide_t(slide, cum_m, cum_s))

    new_content = '--'.join(new_slides)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as fh:
            fh.write(new_content)
        print(f"Updated {file_path}")
