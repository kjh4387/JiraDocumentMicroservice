from datetime import date

class Research:
    def __init__(self, research_key: str, research_name:str, start_date : date, end_date : date):
        self.research_key = research_key
        self.name = research_name
        self.start_date = start_date
        self.end_date = end_date
