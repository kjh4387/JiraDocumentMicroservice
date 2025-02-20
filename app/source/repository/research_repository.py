from domain.research import Research
from datetime import date

class ResearchRepository:
    def get_by_key(self, research_key: str) -> Research:
        #데모 return
        return Research(
            research_key=research_key,
            name="Research Project Example",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
