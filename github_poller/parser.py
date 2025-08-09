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
                # Strip the diff marker (+ or space)
                content = line[1:].lstrip()

                # Start of object
                if content.strip() == '{' and not recording:
                    buffer = ['{']
                    recording = True
                    continue

                if recording:
                    buffer.append(content)

                    # Detect end of object: either '},' or '}'
                    if content.strip() in ('},', '}'):
                        # Clean trailing commas
                        raw = '\n'.join(buffer)
                        # Remove any trailing commas on last property
                        lines = raw.splitlines()
                        # Last line is '}' or '},'
                        # Strip comma if present
                        lines[-1] = lines[-1].rstrip(',')
                        # Also strip trailing comma from previous line if needed
                        if len(lines) >= 2:
                            lines[-2] = lines[-2].rstrip(',')
                        clean = '\n'.join(lines)

                        data = json.loads(clean)
                        jobs.append(JobListing(**data))
                        recording = False

        return jobs
