
import json
import time
from typing import Optional
from pydantic import BaseModel

class Event(BaseModel):
    group: str = 'default'
    group_index: Optional[int] = None
    event: str
    content: Optional[str] = ''
    elapsed: Optional[str] = ''
    group_elapsed: Optional[str] = ''
    start: float
    end: Optional[float] = None

class EventTimeStamp():
    def __init__(self) -> None:
        self.data = []
        self.point()

    def point(self):
        self.start = time.time()

    def add(self, **kwargs):
        if 'start' not in kwargs:
            if 'use_point' in kwargs:
                kwargs['start'] = self.start
                kwargs['end'] = time.time()
            else:
                kwargs['start'] = time.time()
        event = Event(**kwargs)
        self.data.append(event)
        self.point()

    def export(self, path):
        min_time = 0
        max_time = 0
        group_min_time = {}

        for event in self.data:
            if event.group not in group_min_time:
                group_min_time[event.group] = event.start
            new_event = Event(**event.dict())
            if new_event.start > max_time:
                max_time = new_event.start
            if new_event.end is not None and new_event.end > max_time:
                max_time = new_event.end

            if new_event.start < min_time or min_time == 0:
                min_time = new_event.start
            if new_event.end is not None and new_event.end < min_time:
                min_time = new_event.end

        mini_sep = (max_time - min_time) * 0.002
        assert mini_sep > 0

        export_data = []
        for index in range(len(self.data)):
            event = self.data[index]
            export_event = event.dict()
            if event.group_index is not None:
                export_event['group'] = export_event['group'] + f' ({event.group_index})'
                export_event.pop('group_index')
            if event.end is None:
                # this_mini_sep = mini_sep
                # if index + 1 < len(self.data) and self.data[index+1].group == event.group:
                #     this_mini_sep = min(self.data[index+1].start-export_event['start'], mini_sep)
                # export_event['end'] = event.start + this_mini_sep
                export_event['end'] = event.start + mini_sep
                export_event['elapsed'] = '{:.2f} ms'.format((export_event['start'] - min_time) * 1000)
                export_event['group_elapsed'] = '{:.2f} ms'.format((export_event['start'] - group_min_time[event.group]) * 1000)
            else:
                export_event['elapsed'] = '{:.2f} ms'.format((export_event['end'] - min_time) * 1000)
                export_event['group_elapsed'] = '{:.2f} ms'.format((export_event['end'] - group_min_time[event.group]) * 1000)
            export_data.append(export_event)


        print(
            json.dumps(export_data, ensure_ascii=False, indent=2),
            file=open(path, 'w')
        )
        print(f'Export data to {path}')

time_stamp = EventTimeStamp()
