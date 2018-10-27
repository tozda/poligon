from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import date, timedelta
import requests
import platform


"""
    ############################################################################
    This script log in into korty.org service within the context of
    AM Tenis Klub. Then it checks if there are any free courts within
    given date and hour.
    It checks if only full hour is available. Halfs are not regarded

"""


# This shall allow to distinguish between synology and windows
# Windows = Windows, Synology = Linux
os_name = platform.system()

# TODO: Run this on cron
# TODO: Try to run this for several clubs
# wednesday nas no of 1
req_days = ['Tuesday', 'Thursday', 'Saturday']
req_hours = ['9:00', '19:00', '20:00']
# special morning configuration
morning_game_day = 'Saturday'
morning_game_time = '9:00'
secret_filename = 'sekrety.txt'
run_log_filename = 'runlog.txt'
# Constant for text meaning reservation to be made put in href
RESERVE = "Rezerwuj"
# login config
main_url = "https://korty.org/klub/"
club_tag = "am-tenis"
url_params = "/dedykowane?data_grafiku=<YYYY-MM-DD>&dyscyplina=1&strona="
court_url_template = main_url + club_tag + url_params


# map string of day into appropriate day number starting from
# Monday = 0, Tuesday = 1, etc
def days_to_numbers(req_day):
    days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
            "Sunday")

    day_cnt = 0
    # (0 - Monday, 6 - Sunday)
    for day in days:
        if day == req_day:
            return day_cnt
        day_cnt = day_cnt + 1


def send_to_slack(slack_message):
    # configuration for sake of slack
    data = '{"text":"' + slack_message + '"}'

    # open file with our slack token
    secrets = open(secret_filename, 'r')
    slack_token = None
    for secret in secrets:
        secret.find('slack_token')
        if secret:
            slack_token = secret.replace("slack_token = ", "")
            break
    secrets.close()

    headers = {'Content-type': 'application/json', }

    requests.post(slack_token, headers=headers, data=data.encode('utf-8'), )


def translate_days(day_name):
    if day_name == 'Monday':
        return 'poniedziałek'
    elif day_name == 'Tuesday':
        return 'wtorek'
    elif day_name == 'Wednesday':
        return 'środa'
    elif day_name == 'Thursday':
        return 'czwartek'
    elif day_name == 'Friday':
        return 'piątek'
    elif day_name == 'Saturday':
        return 'sobota'
    elif day_name == 'Sunday':
        return 'niedziela'


# chrome webdriver configuration to be run headless
run_headless = 1
# create instance of browser
chrome_options = Options()
chrome_options.add_argument("--headless")
if run_headless == 0:
    driver = webdriver.Chrome()
elif run_headless == 1:
    driver = webdriver.Chrome(options=chrome_options)
else:
    slack_message = 'Browser not correctly configured!\nExiting...!'
    send_to_slack(slack_message)
    exit()

information = []
for req_day in req_days:

    for req_hour in req_hours:

        is_morning_play = 0

        if req_day == morning_game_day and req_hour == morning_game_time:
            is_morning_play = 1
        elif req_day == morning_game_day and is_morning_play == 0:
            break

        requested_day = days_to_numbers(req_day)
        requested_hour = req_hour

        # variable for time slot
        time_slot = None
        # variable for court number
        court_number = None

        play_date = date.today()
        today_name = date.strftime(play_date, '%A')
        no_of_today = date.weekday(play_date)

        # array for messages
        messages = []
        # increment through whole week in order to
        # find next date to be checked
        courts_url = ""

        for i in range(7):
            # increment date of 1
            play_date += timedelta(days=1)
            # get the number of day
            no_of_play_date = date.weekday(play_date)
            # if number of day is equal to the one we are looking for
            # then build ULR end exit

            if no_of_play_date == requested_day:
                courts_url = court_url_template.replace("<YYYY-MM-DD>",
                                                        str(play_date))
                break

        messages.append(play_date)

        # because there are two tabs of courts on
        # AM Tenis we need to go through both
        for tab in range(2):
            court_tab_url = courts_url + str(tab)
            driver.get(court_tab_url)
            # check if you are on the requested site
            # print("Connecting to the website: ", court_tab_url)
            assert "AM Tenis" in driver.title
            table = driver.find_element_by_tag_name("tbody")
            rows = table.find_elements_by_tag_name("tr")
            row_no = 1
            prv_time_slot = None

            for row in rows:
                slot_flag = 0
                hour_flag = 0
                cells = row.find_elements_by_tag_name("td")
                column_no = 1

                for cell in cells:
                    # reset flag showing if something to
                    # be reserved has been found
                    is_free = 0

                    # first TD tag contains time of slot
                    if column_no == 1:
                        time_slot = cell.text

                    # no point to search whole day for look of
                    # morning play
                    if is_morning_play == 1 and time_slot != req_hour:
                        break

                    # if any of cells in given time slot has value of
                    # RESERVE variable
                    # set flag upon this lot
                    if cell.find_elements_by_link_text(RESERVE) and \
                            time_slot == req_hour:
                        messages.append(time_slot)
                    # increment column counter
                    column_no = column_no + 1

        # Clean up duplicated messages
        msg_cnt = 0
        courts_no = 0
        for msg in messages:

            if msg_cnt == 0:
                pass

            if msg == requested_hour:
                courts_no = courts_no + 1
                msg_cnt = msg_cnt + 1

        if courts_no > 0:
            if courts_no == 1:
                con_cort = "kort"
                con_is = 'jest'
            else:
                con_cort = "korty"
                con_is = 'są'
            text_message = str(play_date) + ' (' + translate_days(req_day) + \
                ') ' + str(courts_no) + ' ' + con_cort + ' na ' + \
                str(req_hour) + ' w klubie ' + club_tag.upper() + ' ' + \
                court_tab_url + '\n'
            information.append(text_message)


# read log from last run
run_log = open(run_log_filename, 'r')
run_log_set = set(run_log)  # convert into set in order to find delta
run_log.close()
# find difference between last run and current run comparing messages
delta = [x for x in information if x not in run_log_set]
# check if there is any difference...
is_delta = len(delta)
# ... and if not then say no change
if is_delta == 0:
    send_to_slack('Kortów brak!!!')
else:  # but if this is then send slack messages
    for d in delta:
        send_to_slack(d)

# close browser
driver.quit()

# write log from current run in order to have something to compare to
# when script will be run next time
run_log = open(run_log_filename, 'w')
for info in information:
    run_log.write(info)
run_log.close()