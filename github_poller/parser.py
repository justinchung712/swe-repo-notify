# github_poller/parser.py
import json
from typing import List
from common.models import JobListing


class DiffParser:

    @staticmethod
    def parse_added_listings(diff_lines: List[str]) -> List[JobListing]:
        buffer: List[str] = []
        jobs: List[JobListing] = []
        recording = False

        for line in diff_lines:
            if line.startswith('+') or (recording and line.startswith(' ')):
                # strip the diff marker (+ or space)
                content = line[1:].lstrip()

                # start of object
                if content.strip() == '{' and not recording:
                    buffer = ['{']
                    recording = True
                    continue

                if recording:
                    buffer.append(content)

                    # detect end of object: either '},' or '}'
                    if content.strip() in ('},', '}'):
                        # Clean trailing commas
                        raw = '\n'.join(buffer)
                        # Remove any trailing commas on last property
                        lines = raw.splitlines()
                        # last line is '}' or '},'
                        # strip comma if present
                        lines[-1] = lines[-1].rstrip(',')
                        # also strip trailing comma from previous line if needed
                        if len(lines) >= 2:
                            lines[-2] = lines[-2].rstrip(',')
                        clean = '\n'.join(lines)

                        data = json.loads(clean)
                        jobs.append(JobListing(**data))
                        recording = False

        return jobs
