import schedule
import time
import threading


def scheduleJob():
    print("Sample Job Executed!", flush=True)


schedule.every().day.at("22:09", "America/New_York").do(scheduleJob)


def ScheduleThread():
    while True:
        schedule.run_pending()
        time.sleep(1)


thread = threading.Thread(target=ScheduleThread, daemon=True)
thread.start()

while True:
    time.sleep(1)
