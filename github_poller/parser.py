import json
import re
from dataclasses import fields
from typing import List
from common.models import JobListing

_TRAILING_COMMA_RE = re.compile(
    r",\s*([}\]])")  # Remove trailing comma before } or ]


class DiffParser:

    @staticmethod
    def parse_added_listings(diff_lines: List[str]) -> List[JobListing]:
        jobs: List[JobListing] = []
        allowed = {f.name for f in fields(JobListing)}

        i = 0
        n = len(diff_lines)

        while i < n:
            line = diff_lines[i]

            # Only begin when seeing an added line that opens an object
            if line.startswith("+"):
                content = line[1:].lstrip()
                if content.strip().startswith("{"):
                    # Start capturing the JSON object
                    buf: List[str] = [content]
                    depth = content.count("{") - content.count("}")

                    i += 1
                    # Collect until the brace depth returns to zero
                    while i < n and depth > 0:
                        l = diff_lines[i]
                        if l.startswith("+") or l.startswith(" "):
                            c = l[1:].lstrip()
                            buf.append(c)
                            depth += c.count("{")
                            depth -= c.count("}")
                        i += 1

                    # Buffer should be a JSON object
                    raw = "\n".join(buf)

                    # Normalize trailing comma before } or ]
                    clean = _TRAILING_COMMA_RE.sub(r"\1", raw)

                    # If last non-empty line is '},' or '}] ,' etc., strip commas
                    lines = [ln.rstrip() for ln in clean.splitlines()]
                    if lines:
                        # Strip trailing commas on the final line
                        lines[-1] = lines[-1].rstrip(",")
                        # Also on the penultimate line
                        if len(lines) >= 2:
                            lines[-2] = lines[-2].rstrip(",")

                    clean = "\n".join(lines)

                    try:
                        data = json.loads(clean)
                    except json.JSONDecodeError:
                        # Skip malformed fragments quietly
                        continue

                    if not isinstance(data, dict):
                        continue

                    # Filter unknown fields (e.g., 'terms') and ensure defaults
                    filtered = {k: v for k, v in data.items() if k in allowed}
                    if "locations" not in filtered or filtered[
                            "locations"] is None:
                        filtered["locations"] = []

                    try:
                        jobs.append(JobListing(**filtered))
                    except TypeError:
                        # Missing required fields / wrong types -> skip
                        pass

                    # Continue loop without incrementing i here
                    continue

            # Not a start of object -> advance
            i += 1

        return jobs
