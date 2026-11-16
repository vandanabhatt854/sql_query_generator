"""A deliberately bounded offline grammar. Unknown requests never become SELECT-all."""
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_today():
    name = os.getenv('APP_TIMEZONE', 'Asia/Kolkata')
    try:
        zone = ZoneInfo(name)
    except ZoneInfoNotFoundError:
        # Windows may not have an IANA database. India has no DST.
        if name not in {'Asia/Kolkata', 'Asia/Calcutta'}:
            raise QueryRequestError('Install tzdata on the backend to use the configured APP_TIMEZONE.', 'configuration', 503) from None
        zone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(zone).date()


class QueryRequestError(ValueError):
    def __init__(self, message, code='clarification', status_code=422):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class OfflineQuery:
    def __init__(self, schema, today=None):
        self.schema = schema
        self.today = today or local_today()

    def fail(self):
        raise QueryRequestError('Please specify the records, fields and conditions you need. This wording needs AI mode; configure ANTHROPIC_API_KEY or GOOGLE_API_KEY in backend/.env to enable broader English requests.')

    def table(self, name):
        matches = [table for table in self.schema if table.lower().rstrip('s') == name.lower().rstrip('s')]
        if len(matches) != 1:
            raise QueryRequestError(f'The database does not contain {name}. Available data: ' + ', '.join(self.schema) + '.', 'unsupported')
        return matches[0]

    def column(self, table, name):
        name = {'gpa': 'cgpa', 'hire date': 'join_date', 'join date': 'join_date'}.get(name, name)
        names = {col['name'].lower(): col['name'] for col in self.schema[table]['columns']}
        if name not in names:
            raise QueryRequestError(f'{table} does not contain a {name} field. Available fields: ' + ', '.join(names) + '.', 'unsupported')
        return names[name]

    def fields(self, table):
        return ', '.join('"' + col['name'] + '"' for col in self.schema[table]['columns'])

    def generate(self, request):
        text = re.sub(r'\s+', ' ', request.strip().lower()).rstrip('?.!')
        text = re.sub(r'^(?:(?:please|kindly) |(?:can|could) you |i (?:want|would like) to )+', '', text)
        text = re.sub(r'^(?:what is|what\x27s|calculate|tell me|show me|show|get|find|display|list|fetch)\s+(?:the\s+)?', '', text)
        text = re.sub(r'\s*\u20b9\s*', ' ', text)
        subjects = r'employee(?:s)?|student(?:s)?|department(?:s)?|customer(?:s)?|order(?:s)?|product(?:s)?'
        # Salary uniquely identifies Employee in the supplied demo schema.
        if re.fullmatch(r'who (?:earns|makes|gets paid) (?:the )?most', text):
            table = self.table('employees')
            col = self.column(table, 'salary')
            return f'SELECT {self.fields(table)} FROM "{table}" WHERE "{col}" = (SELECT MAX("{col}") FROM "{table}");'
        aggregate = re.fullmatch(rf'(?:the )?(average|avg|total|sum|maximum|max|minimum|min|highest|lowest)(?: of)? (salary|cgpa|gpa|semester|price|amount)(?: (?:of|for) (?:all )?({subjects}))?(?: (?:in|for|by|per) (?:each |every )?(department|course))?', text)
        if aggregate:
            operation, field, subject, group = aggregate.groups()
            if subject:
                table = self.table(subject)
            else:
                matches = [t for t, meta in self.schema.items() if any(c['name'].lower() == ('cgpa' if field == 'gpa' else field) for c in meta['columns'])]
                if len(matches) != 1:
                    self.fail()
                table = matches[0]
            col = self.column(table, field)
            function = {'average': 'AVG', 'avg': 'AVG', 'total': 'SUM', 'sum': 'SUM', 'maximum': 'MAX', 'max': 'MAX', 'highest': 'MAX', 'minimum': 'MIN', 'min': 'MIN', 'lowest': 'MIN'}[operation]
            grouping = self.column(table, group) if group else None
            return f'SELECT ' + (f'"{grouping}", ' if grouping else '') + f'{function}("{col}") AS "{function.lower()}_{col}" FROM "{table}"' + (f' GROUP BY "{grouping}"' if grouping else '') + ';'
        count = re.fullmatch(rf'(?:count(?: how many| of)?|how many|number of|total number of) ({subjects})(?: (?:are )?(?:in|by|per) (?:each |every )?(department|course))?', text)
        if count:
            subject, group = count.groups()
            table = self.table(subject)
            grouping = self.column(table, group) if group else None
            return 'SELECT ' + (f'"{grouping}", ' if grouping else '') + f'COUNT(*) AS total_count FROM "{table}"' + (f' GROUP BY "{grouping}"' if grouping else '') + ';'
        top = re.fullmatch(rf'top (\d+) (?:highest paid|highest-paid) ({subjects})(?: in the company)?', text)
        if top:
            limit, subject = top.groups()
            table = self.table(subject)
            col = self.column(table, 'salary')
            if not 1 <= int(limit) <= 1000:
                self.fail()
            return f'SELECT {self.fields(table)} FROM "{table}" ORDER BY "{col}" DESC LIMIT {int(limit)};'
        rows = re.fullmatch(rf'(?:all )?({subjects})(.*)', text)
        if not rows:
            self.fail()
        subject, remainder = rows.groups()
        table = self.table(subject)
        remainder = remainder.strip()
        base = f'SELECT {self.fields(table)} FROM "{table}"'
        if not remainder:
            return base + ';'
        # Fully match the remaining condition, so extra AND/OR restrictions cannot be ignored.
        department = re.fullmatch(r'(?:from|in) (?:the )?([a-z]+) department', remainder)
        if department:
            col = self.column(table, 'department')
            return base + f' WHERE "{col}" = \'{department[1]}\' COLLATE NOCASE;'
        if re.fullmatch(r'(?:who )?(?:joined|hired|were hired) last year', remainder):
            col = self.column(table, 'join_date')
            year = self.today.year - 1
            return base + f' WHERE "{col}" >= \'{year}-01-01\' AND "{col}" < \'{year + 1}-01-01\';'
        years = re.fullmatch(r'(?:who )?(?:joined|hired|were hired) between (\d{4}) and (\d{4})', remainder)
        if years:
            start, end = map(int, years.groups())
            if start > end or end >= 9999:
                raise QueryRequestError('The start year must not be later than the end year, and the end year must be below 9999.')
            col = self.column(table, 'join_date')
            return base + f' WHERE "{col}" >= \'{start}-01-01\' AND "{col}" < \'{end + 1}-01-01\';'
        prefix = re.fullmatch(r'(?:whose |with |where )?name (?:is )?(?:starting|starts|beginning|begins) with [\x27\"]?([a-z0-9]+)[\x27\"]?', remainder)
        if prefix:
            col = self.column(table, 'name')
            return base + f' WHERE "{col}" LIKE \'{prefix[1]}%\';'
        course = re.fullmatch(r'enrolled in ([a-z ]+?)(?: with grade ([a-z]) or ([a-z]))?', remainder)
        if course:
            name, first, second = course.groups()
            col = self.column(table, 'course')
            condition = f'"{col}" = \'{name}\' COLLATE NOCASE'
            if first:
                grade = self.column(table, 'grade')
                condition += f' AND "{grade}" IN (\'{first.upper()}\', \'{second.upper()}\')'
            return base + ' WHERE ' + condition + ';'
        numeric = re.fullmatch(r'(?:whose |with |where )?(salary|cgpa|gpa|semester|price|amount)(?: is)? (greater than|more than|above|over|at least|less than|below|under|at most|equal to|equals|>=|<=|>|<|=) ([0-9][0-9,]*(?:\.[0-9]+)?)(?:\s*(k|m|lakh|lakhs|crore|crores))?', remainder)
        if numeric:
            field, comparison, value, unit = numeric.groups()
            col = self.column(table, field)
            multiplier = {'k': 1000, 'm': 1000000, 'lakh': 100000, 'lakhs': 100000, 'crore': 10000000, 'crores': 10000000}.get(unit, 1)
            value = float(value.replace(',', '')) * multiplier
            operators = {'greater than': '>', 'more than': '>', 'above': '>', 'over': '>', 'at least': '>=', 'less than': '<', 'below': '<', 'under': '<', 'at most': '<=', 'equal to': '=', 'equals': '='}
            return base + f' WHERE "{col}" {operators.get(comparison, comparison)} {value:g};'
        self.fail()
