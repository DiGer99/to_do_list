# функция проверки, есть ли "-" между временем, т.е. "11:30-12:30"
async def check_dash_in_time(rows: list) -> bool:
    for i in rows:
        if "-" in i:
            return True
    return False