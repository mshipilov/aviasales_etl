from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def parse_russian_date(date_str):
    """
    Extract date from string with format '11 янв, сб'
    """
    # Map Russian month names to month numbers
    russian_months = {
        "янв": "1", "фев": "2", "мар": "3", "апр": "4",
        "мая": "5", "май": "5", "июн": "6", "июл": "7", "авг": "8",
        "сен": "9", "окт": "10", "ноя": "11", "дек": "12"
    }
    
    # Split the input string
    parts = date_str.split()
    day = parts[0]
    month_name = parts[1].lower().replace(',', '')
    month_name = month_name[:3]  # take only first 3 letters to hand changes on frontend
    
    # Get the month number from our dictionary
    month_num = russian_months.get(month_name)
    if not month_num:
        raise ValueError(f"Unknown month: {month_name}")
    
    # Use the current year as a default
    current_year = date.today().year
    result_date = date(current_year, int(month_num), int(day))

    # if result date < now, use next year
    if result_date < date.today():
        #result_date = result_date + timedelta(days=365)  # ignore 366 days in year for simplicity
        result_date = result_date + relativedelta(years=1)
        
    
    return result_date
