#!/Users/Yaxin.Cheng@iCloud.com/Developer/venv/bin/python
import sys, argparse, re, pytz, copy
from datetime import datetime, timedelta
from ics import Calendar, Event

parser = argparse.ArgumentParser(description='Convert file to ics')
parser.add_argument('file', help='File location')
args = parser.parse_args()

nameRegex = re.compile('[A-Z]{4} \d{4} .+')
dateRegex = re.compile('\d{2}\-\w{3}\-\d{4}\s\-\s\d{2}\-\w{3}\-\d{4}')
contRegex = re.compile('\d{5}\s*?(Lec|Lab|Tut|WkT|Ths)\s*?[MTWRF]+\s*?\d{4}-\d{4}')

def dateRange(begin, end):
    current = copy.copy(begin)
    while current < end:
        yield current
        current += timedelta(days=1)

class Course:
    def __init__(self, name, content, pre, post):
        (_, type, weeks, time) = content.split('\t')
        self.name = name if type == 'Lec' else name + ' ' + type
        weeksMap = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4}
        self.weeks = set(map(lambda w: weeksMap[w], weeks))
        self.begin, self.end = [int(element) for element in time.split('-')]
        self.pre, self.post = pre, post

    def toEvent(self, date):
        global hfxZone
        e = Event(name=self.name)
        e.begin = date.replace(hour=int(self.begin/100), minute=int(self.begin%100), second=0)
        e.end   = date.replace(hour=int(self.end / 100), minute=int(self.end % 100), second=0)
        return e

    def __hash__(self):
        return hash(self.name)
    
    def __repr__(self):
        return self.name + '\n' + str(self.begin) + '\t' + str(self.end)

courseMapping = [set() for _ in range(5)]
minDate = None
maxDate = None
hfxZone = pytz.timezone('America/Halifax')

with open(args.file) as inFile:
    calendar = Calendar()
    for piece in inFile.readlines():
        if nameRegex.match(piece) is not None:
            name = nameRegex.match(piece).group()
        elif dateRegex.match(piece) is not None:
            date = dateRegex.match(piece).group()
            pre, post = [hfxZone.localize(datetime.strptime(each.strip(), '%d-%b-%Y')) for each in date.split(' - ')]
            if minDate is None or minDate > pre:  minDate = pre
            if maxDate is None or maxDate < post: maxDate = post
        elif contRegex.match(piece) is not None:
            content = contRegex.match(piece).group()
            try: course = Course(name, content, pre, post)
            except ValueError: continue
            for week in course.weeks: courseMapping[week].add(course)

calendar = Calendar()
for date in dateRange(minDate, maxDate):
    if date.weekday() in (5, 6): continue
    courses = courseMapping[date.weekday()]
    events = [course.toEvent(date) for course in courses if course.pre <= date and course.post > date]
    calendar.events += events

#for index, each in enumerate(courseMapping):
#    print('weekdays: ', index)
#    print(each)
#    print()

with open('dal.ics', 'w') as f: f.writelines(calendar)